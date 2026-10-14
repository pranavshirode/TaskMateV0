import type { IconName } from "@/components/ui/Icon";

export interface NavItem {
  name: string;
  href: string;
  icon: IconName;
  description: string;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

export const NAV_SECTIONS: NavSection[] = [
  {
    title: "Work",
    items: [
      {
        name: "Today",
        href: "/",
        icon: "today",
        description: "Your focus for today",
      },
      {
        name: "Tasks",
        href: "/tasks",
        icon: "tasks",
        description: "All tasks, list or board",
      },
      {
        name: "Projects",
        href: "/projects",
        icon: "folder",
        description: "Projects and their progress",
      },
      {
        name: "Clients",
        href: "/clients",
        icon: "users",
        description: "Client relationships",
      },
    ],
  },
  {
    title: "AI",
    items: [
      {
        name: "AI Assistant",
        href: "/ai",
        icon: "sparkles",
        description: "Ask or tell TaskMate to do things",
      },
      {
        name: "Requirements",
        href: "/requirements",
        icon: "requirements",
        description: "Turn client briefs into tasks",
      },
    ],
  },
  {
    title: "Workspace",
    items: [
      {
        name: "Repositories",
        href: "/repositories",
        icon: "repo",
        description: "Linked code repositories",
      },
      {
        name: "Settings",
        href: "/settings",
        icon: "settings",
        description: "Profile and integrations",
      },
    ],
  },
];

export const ALL_NAV_ITEMS = NAV_SECTIONS.flatMap((s) => s.items);

export function isNavActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  // The legacy /assistant route is the same experience as /ai.
  if (href === "/ai" && pathname.startsWith("/assistant")) return true;
  return pathname === href || pathname.startsWith(href + "/");
}
