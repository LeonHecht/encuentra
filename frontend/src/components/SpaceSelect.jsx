import { useSpaces } from "@/hooks/useSpaces";

export default function SpaceSelect({ value, onChange, allowCreate = false, ...rest }) {
  const { spaces, loading, label, user } = useSpaces();

  if (loading) return <div>Loading spaces…</div>;
  if (!spaces.length) return <div>No spaces available</div>;

  // ----- split into groups -----
  const groups = {
    public:       [],
    personal:     [],
    organization: [],
  };

  spaces.forEach((s) => {
    if (!s.includes("/"))                     groups.public.push(s);
    else if (s.startsWith(`${user.email}/`))  groups.personal.push(s);
    else                                       groups.organization.push(s);
  });

  return (
    <select value={value} onChange={e => onChange(e.target.value)} {...rest}>
      {groups.public.length > 0 && (
        <optgroup label="Public">
          {groups.public.map((s) => (
            <option key={s} value={s}>{label(s)}</option>
          ))}
        </optgroup>
      )}

      {groups.personal.length > 0 && (
        <optgroup label="Personal">
          {groups.personal.map((s) => (
            <option key={s} value={s}>{label(s)}</option>
          ))}
        </optgroup>
      )}
      
      {groups.organization.length > 0 && (
        <optgroup label="Organisation">
          {groups.organization.map((s) => (
            <option key={s} value={s}>{label(s)}</option>
          ))}
        </optgroup>
      )}
      {allowCreate && (
        <option key="__new__" value="__new__">
          ➕ New space…
        </option>
      )}
    </select>
  );
}
