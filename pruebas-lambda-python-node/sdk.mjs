// El SDK v3 que ya trae la imagen de Lambda (no se instala nada).
import { S3Client } from "@aws-sdk/client-s3";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";

// Fuera del handler: se ejecuta en el INIT, una vez por entorno, como recomienda AWS.
const s3 = new S3Client({ region: "us-east-1" });
const dynamo = new DynamoDBClient({ region: "us-east-1" });
let invocaciones = 0;

function suma(n) {
  let s = 0;
  for (let i = 1; i <= n; i++) s += (i * i) % 1000003;
  return s;
}

export const handler = async (event) => {
  invocaciones++;
  // No llama a AWS: solo comprueba que los clientes existen. Mide el coste de cargarlos.
  const clientes = [s3.config.serviceId.toLowerCase(), dynamo.config.serviceId.toLowerCase()];
  return { lang: "node", fn: "sdk", suma: suma(10000), clientes, invocacion: invocaciones };
};
