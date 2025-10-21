import { useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";
import { supabase } from "@/lib/supabaseClient";

type Chat = {
  id: string;
  title: string | null;
  created_at: string;
};

export type ChatSidebarProps = {
  selectedId: string | null;
  onSelect: (id: string) => void;
  onCreated?: (id: string) => void;
  className?: string;
};

export default function ChatSidebar({
  selectedId,
  onSelect,
  onCreated,
  className,
}: ChatSidebarProps) {
  const [open, setOpen] = useState(true);
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchChats = useCallback(async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from("chats")
      .select("id,title,created_at")
      .order("created_at", { ascending: false });
    if (!error && data) setChats(data as Chat[]);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchChats();
  }, [fetchChats]);

  const createChat = useCallback(async () => {
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) return;

    const { data, error } = await supabase
      .from("chats")
      .insert({
        user_id: user.id,
        title: "Nuevo chat",
      })
      .select()
      .single();

    if (!error && data) {
      setChats((prev) => [data as Chat, ...prev]);
      onCreated?.(data.id);
      onSelect(data.id);
    }
  }, [onCreated, onSelect]);

  return (
    <div
      className={cn(
        "flex h-full w-72 flex-col border-r bg-white",
        className
      )}
    >
      <Collapsible open={open} onOpenChange={setOpen} className="flex flex-col">
        <div className="flex items-center justify-between border-b p-3">
          <CollapsibleTrigger asChild>
            <Button variant="ghost" className="px-2 font-semibold">
              Chats
            </Button>
          </CollapsibleTrigger>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={fetchChats}
              variant="ghost"
              disabled={loading}
            >
              {loading ? "…" : "↻"}
            </Button>
            <Button size="sm" onClick={createChat}>
              + Nuevo
            </Button>
          </div>
        </div>

        <CollapsibleContent className="flex-1 overflow-hidden">
          <ScrollArea className="h-[calc(100vh-8rem)] px-2 pb-2">
            <div className="flex flex-col gap-1 pr-2 pt-2">
              {chats.map((c) => (
                <Button
                  key={c.id}
                  variant="ghost"
                  className={cn(
                    "w-full justify-start rounded-lg px-3 text-left",
                    selectedId === c.id && "bg-accent"
                  )}
                  onClick={() => onSelect(c.id)}
                >
                  <span className="truncate">
                    {c.title || "Sin título"}
                  </span>
                </Button>
              ))}
              {chats.length === 0 && !loading && (
                <div className="px-3 py-2 text-sm text-muted-foreground">
                  No hay chats todavía.
                </div>
              )}
            </div>
          </ScrollArea>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}
