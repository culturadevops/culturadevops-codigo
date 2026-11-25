let invocaciones = 0;

function suma(n) {
  let s = 0;
  for (let i = 1; i <= n; i++) s += (i * i) % 1000003;
  return s;
}

export const handler = async (event) => {
  invocaciones++;
  return { lang: "node", fn: "simple", suma: suma(10000), invocacion: invocaciones };
};
