"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { usePathname } from "next/navigation";
import { HomeIcon, MessageSquareTextIcon } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";

type ServerStatus = "checking" | "online" | "offline";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.trim() || "http://localhost:8000";

export function OracleSidebar() {
  const pathname = usePathname();
  const [status, setStatus] = useState<ServerStatus>("checking");

  const links = useMemo(
    () => [
      { href: "/", label: "Home", icon: HomeIcon },
      { href: "/chat", label: "Chat", icon: MessageSquareTextIcon },
    ],
    [],
  );

  useEffect(() => {
    let isActive = true;
    const controller = new AbortController();

    const checkHealth = async () => {
      setStatus("checking");
      try {
        const response = await fetch(`${API_BASE}/`, {
          method: "GET",
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const payload = (await response.json()) as { Hello?: string };
        if (payload?.Hello !== "World") {
          throw new Error("Unexpected response");
        }
        if (isActive) {
          setStatus("online");
        }
      } catch {
        if (!isActive) {
          return;
        }
        setStatus("offline");
      }
    };

    void checkHealth();

    return () => {
      isActive = false;
      controller.abort();
    };
  }, []);

  return (
    <Sidebar variant="inset" collapsible="icon">
      <SidebarHeader className="group-data-[collapsible=icon]:hidden">
        <div className="flex flex-col gap-1 px-2 py-1">
          <span className="text-base font-semibold text-primary">
            Card Oracle
          </span>
          <span className="text-xs text-muted-foreground">
            Magic: The Gathering
          </span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {links.map((link) => {
                const isActive = pathname === link.href;
                const Icon = link.icon;
                return (
                  <SidebarMenuItem key={link.href}>
                    <SidebarMenuButton asChild isActive={isActive}>
                      <Link href={link.href}>
                        <Icon />
                        <span>{link.label}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <p
          className={cn([
            "w-full rounded-md px-3 py-2 text-xs font-semibold uppercase tracking-wider",
            "group-data-[collapsible=icon]:hidden",
            status === "online"
              ? "bg-emerald-500/20 text-emerald-700"
              : status === "offline"
                ? "bg-destructive/15 text-destructive"
                : "bg-muted text-muted-foreground",
          ])}
          aria-live="polite"
        >
          {status === "online"
            ? "API Online"
            : status === "offline"
              ? "API Offline"
              : "API Checking"}
        </p>
      </SidebarFooter>
    </Sidebar>
  );
}
