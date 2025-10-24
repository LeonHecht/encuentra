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

  // Listen for local UI events to keep list in sync without a full reload
  useEffect(() => {
    const handleChatUpdated = (e: Event) => {
      const evt = e as CustomEvent<{ id: string; title?: string }>; 
      const { id, title } = evt.detail || ({} as any);
      if (!id) return;
      setChats((prev) =>
        prev.map((c) => (c.id === id ? { ...c, title: title ?? c.title } : c))
      );
    };

    const handleChatCreated = (e: Event) => {
      const evt = e as CustomEvent<{ chat: Chat }>; 
      const chat = evt.detail?.chat;
      if (!chat) return;
      setChats((prev) => {
        if (prev.some((c) => c.id === chat.id)) return prev;
        return [chat, ...prev];
      });
    };

    window.addEventListener("chat:updated", handleChatUpdated as EventListener);
    window.addEventListener("chat:created", handleChatCreated as EventListener);
    return () => {
      window.removeEventListener(
        "chat:updated",
        handleChatUpdated as EventListener
      );
      window.removeEventListener(
        "chat:created",
        handleChatCreated as EventListener
      );
    };
  }, []);

  // Optional: subscribe to Supabase Realtime so updates from other tabs/processes also reflect instantly
  useEffect(() => {
    let channel: any;
    (async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) return;
      channel = supabase
        .channel("realtime:chats")
        .on(
          "postgres_changes",
          { event: "INSERT", schema: "public", table: "chats", filter: `user_id=eq.${user.id}` },
          (payload) => {
            const chat = payload.new as Chat;
            setChats((prev) => {
              if (prev.some((c) => c.id === chat.id)) return prev;
              return [chat, ...prev];
            });
          }
        )
        .on(
          "postgres_changes",
          { event: "UPDATE", schema: "public", table: "chats", filter: `user_id=eq.${user.id}` },
          (payload) => {
            const chat = payload.new as Chat;
            setChats((prev) =>
              prev.map((c) =>
                c.id === chat.id
                  ? { ...c, title: chat.title, updated_at: chat.updated_at }
                  : c
              )
            );
          }
        )
        .on(
          "postgres_changes",
          { event: "DELETE", schema: "public", table: "chats", filter: `user_id=eq.${user.id}` },
          (payload) => {
            const oldId = (payload.old as any)?.id as string | undefined;
            if (!oldId) return;
            setChats((prev) => prev.filter((c) => c.id !== oldId));
          }
        )
        .subscribe();
    })();

    return () => {
      if (channel) {
        try {
          supabase.removeChannel(channel);
        } catch {}
      }
    };
  }, []);

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