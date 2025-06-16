export function formatSpaceLabel(space, { email, organization }) {
  // public corpus: no slash
  if (!space.includes("/")) return space;

  const [owner, name] = space.split("/");

  if (owner === email)            return `personal/${name}`;
  if (owner === organization)     return `${owner}/${name}`;   // org space
  return `${owner}/${name}`;                                   // other shared space
}
