import { useEffect, useState, useCallback } from "react";
import { supabase } from "@/lib/supabaseClient";
import { Button } from "@/components/ui/button";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

type Chat = {
  id: string;
  title: string | null;
  created_at: string;
  updated_at?: string;
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
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchChats = useCallback(async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from("chats")
      .select("id,title,created_at,updated_at")
      .order("updated_at", { ascending: false })
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
    <Sidebar
      className={className}
      // Use CSS var with fallback, so it adapts to navbar height dynamically
      style={{
        top: "var(--navbar-h, 4rem)",
        height: "calc(100vh - var(--navbar-h, 4rem))",
      }}
    >
      {/* Keep header sticky so actions stay visible while scrolling */}
      <SidebarHeader className="sticky top-0 z-10 border-b bg-background/80 backdrop-blur">
        <div className="flex items-center justify-between px-3 py-2">
          <span className="font-semibold">Chats</span>
          <div className="flex items-center gap-2">
            {/* Removed reload button as requested */}
            <Button size="sm" onClick={createChat} disabled={loading}>
              + Nuevo
            </Button>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Historial de Chats</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {chats.map((c) => (
                <SidebarMenuItem key={c.id}>
                  <SidebarMenuButton
                    isActive={selectedId === c.id}
                    onClick={() => onSelect(c.id)}
                  >
                    <span className="truncate">{c.title || "Sin título"}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
              {chats.length === 0 && !loading && (
                <div className="px-3 py-2 text-sm text-muted-foreground">
                  No hay chats todavía.
                </div>
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}