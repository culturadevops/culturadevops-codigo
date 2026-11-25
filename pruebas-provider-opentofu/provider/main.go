// Un proveedor de OpenTofu de laboratorio, con el protocolo de verdad.
//
// Gestiona un recurso TANGIBLE: un fichero en disco con un contenido. Se eligió a propósito algo
// que se puede mirar con `cat` y tocar a mano, para que el desvío del punto 5 sea visible.
//
// ⛔ Es un proveedor de laboratorio. No maneja importación, ni recursos que se renombran, ni
//    reintentos, ni las mil cosas que necesita uno de producción. El objetivo es ver el mecanismo.
package main

import (
	"context"
	"os"
	"path/filepath"

	"github.com/hashicorp/terraform-plugin-framework/datasource"
	"github.com/hashicorp/terraform-plugin-framework/provider"
	"github.com/hashicorp/terraform-plugin-framework/provider/schema"
	"github.com/hashicorp/terraform-plugin-framework/resource"
	rschema "github.com/hashicorp/terraform-plugin-framework/resource/schema"
	"github.com/hashicorp/terraform-plugin-framework/types"
	"github.com/hashicorp/terraform-plugin-go/tfprotov6"
	"github.com/hashicorp/terraform-plugin-go/tfprotov6/tf6server"
	"github.com/hashicorp/terraform-plugin-framework/providerserver"
)

// ─────────────────────────── el proveedor ───────────────────────────

type ficheritoProvider struct{}

func (p *ficheritoProvider) Metadata(_ context.Context, _ provider.MetadataRequest, r *provider.MetadataResponse) {
	r.TypeName = "ficherito"
	r.Version = "0.1.0"
}

func (p *ficheritoProvider) Schema(_ context.Context, _ provider.SchemaRequest, r *provider.SchemaResponse) {
	r.Schema = schema.Schema{}
}

func (p *ficheritoProvider) Configure(_ context.Context, _ provider.ConfigureRequest, _ *provider.ConfigureResponse) {
}

func (p *ficheritoProvider) Resources(_ context.Context) []func() resource.Resource {
	return []func() resource.Resource{func() resource.Resource { return &ficheroResource{} }}
}

func (p *ficheritoProvider) DataSources(_ context.Context) []func() datasource.DataSource {
	return nil
}

// ─────────────────────────── el recurso ───────────────────────────

type ficheroModel struct {
	Ruta      types.String `tfsdk:"ruta"`
	Contenido types.String `tfsdk:"contenido"`
	ID        types.String `tfsdk:"id"`
}

type ficheroResource struct{}

func (r *ficheroResource) Metadata(_ context.Context, req resource.MetadataRequest, resp *resource.MetadataResponse) {
	resp.TypeName = req.ProviderTypeName + "_fichero"
}

func (r *ficheroResource) Schema(_ context.Context, _ resource.SchemaRequest, resp *resource.SchemaResponse) {
	resp.Schema = rschema.Schema{
		Attributes: map[string]rschema.Attribute{
			"ruta":      rschema.StringAttribute{Required: true},
			"contenido": rschema.StringAttribute{Required: true},
			"id":        rschema.StringAttribute{Computed: true},
		},
	}
}

// Create — lo que corre en el `apply` cuando el recurso no existe en el estado.
func (r *ficheroResource) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
	var m ficheroModel
	resp.Diagnostics.Append(req.Plan.Get(ctx, &m)...)
	if resp.Diagnostics.HasError() {
		return
	}
	ruta := m.Ruta.ValueString()
	if err := os.MkdirAll(filepath.Dir(ruta), 0o755); err != nil {
		resp.Diagnostics.AddError("no pude crear el directorio", err.Error())
		return
	}
	if err := os.WriteFile(ruta, []byte(m.Contenido.ValueString()), 0o644); err != nil {
		resp.Diagnostics.AddError("no pude escribir el fichero", err.Error())
		return
	}
	m.ID = types.StringValue(ruta)
	resp.Diagnostics.Append(resp.State.Set(ctx, &m)...)
}

// Read — ⛔ ESTA es la función que descubre el desvío. OpenTofu la llama ANTES del plan para
// preguntarle al mundo real cómo está la cosa, y luego compara ese resultado con la configuración.
// Si aquí devolvieras siempre lo que dice el estado, el desvío no se vería NUNCA.
func (r *ficheroResource) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {
	var m ficheroModel
	resp.Diagnostics.Append(req.State.Get(ctx, &m)...)
	if resp.Diagnostics.HasError() {
		return
	}
	datos, err := os.ReadFile(m.Ruta.ValueString())
	if err != nil {
		// Ya no está: se quita del estado y OpenTofu lo planificará como creación.
		resp.State.RemoveResource(ctx)
		return
	}
	m.Contenido = types.StringValue(string(datos))
	resp.Diagnostics.Append(resp.State.Set(ctx, &m)...)
}

func (r *ficheroResource) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
	var m ficheroModel
	resp.Diagnostics.Append(req.Plan.Get(ctx, &m)...)
	if resp.Diagnostics.HasError() {
		return
	}
	if err := os.WriteFile(m.Ruta.ValueString(), []byte(m.Contenido.ValueString()), 0o644); err != nil {
		resp.Diagnostics.AddError("no pude escribir el fichero", err.Error())
		return
	}
	m.ID = types.StringValue(m.Ruta.ValueString())
	resp.Diagnostics.Append(resp.State.Set(ctx, &m)...)
}

func (r *ficheroResource) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
	var m ficheroModel
	resp.Diagnostics.Append(req.State.Get(ctx, &m)...)
	if resp.Diagnostics.HasError() {
		return
	}
	if err := os.Remove(m.Ruta.ValueString()); err != nil && !os.IsNotExist(err) {
		resp.Diagnostics.AddError("no pude borrar el fichero", err.Error())
	}
}

// ─────────────────────────── el servidor ───────────────────────────

func main() {
	srv := providerserver.NewProtocol6(&ficheritoProvider{})
	_ = tf6server.Serve("registry.opentofu.org/lab/ficherito",
		func() tfprotov6.ProviderServer { return srv() })
}
