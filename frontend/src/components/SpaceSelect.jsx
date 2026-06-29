import { useEffect } from "react";
import { useSpaces } from "@/hooks/useSpaces";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

function isPublicSpace(space) {
  return typeof space === "string" && !space.includes("/");
}

export default function SpaceSelect({
  value,
  onChange,
  allowCreate = false,
  placeholder = "Selecciona un espacio…",
  className,
  ...rest
}) {
  const { spaces, loading, label, user } = useSpaces();

  const canonicalPublicSpace = spaces.find(isPublicSpace);

  useEffect(() => {
    if (
      !loading &&
      canonicalPublicSpace &&
      value &&
      isPublicSpace(value) &&
      value !== canonicalPublicSpace &&
      typeof onChange === "function"
    ) {
      onChange(canonicalPublicSpace);
    }
  }, [canonicalPublicSpace, loading, onChange, value]);

  if (loading && !spaces.length) return <div className="text-sm text-muted-foreground">Cargando espacios…</div>;
  if (!spaces.length) return <div className="text-sm text-muted-foreground">Sin espacios disponibles</div>;

  // ----- split into groups -----
  const groups = {
    public: [],
    personal: [],
    organization: [],
  };

  spaces.forEach((s) => {
    if (!s.includes("/")) groups.public.push(s);
    else if (user?.email && s.startsWith(`${user.email}/`)) groups.personal.push(s);
    else groups.organization.push(s);
  });

  return (
    <Select value={value} onValueChange={onChange} {...rest}>
      <SelectTrigger className={cn("w-[16rem]", className)}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {groups.public.length > 0 && (
          <SelectGroup>
            <SelectLabel>Público</SelectLabel>
            {groups.public.map((s) => (
              <SelectItem key={s} value={s}>
                {label(s)}
              </SelectItem>
            ))}
          </SelectGroup>
        )}
        {groups.personal.length > 0 && (
          <>
            <SelectSeparator />
            <SelectGroup>
              <SelectLabel>Personal</SelectLabel>
              {groups.personal.map((s) => (
                <SelectItem key={s} value={s}>
                  {label(s)}
                </SelectItem>
              ))}
            </SelectGroup>
          </>
        )}
        {groups.organization.length > 0 && (
          <>
            <SelectSeparator />
            <SelectGroup>
              <SelectLabel>Organisation</SelectLabel>
              {groups.organization.map((s) => (
                <SelectItem key={s} value={s}>
                  {label(s)}
                </SelectItem>
              ))}
            </SelectGroup>
          </>
        )}
        {allowCreate && (
          <>
            <SelectSeparator />
            <SelectItem value="__new__">➕ New space…</SelectItem>
          </>
        )}
      </SelectContent>
    </Select>
  );
}
