import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { AdminNavigation } from "./AdminNavigation";

describe("AdminNavigation", () => {
  it("将填写记录、生成任务、报告和审计日志分开导航", () => {
    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <AdminNavigation />
      </MemoryRouter>
    );

    expect(screen.getByRole("link", { name: "总览" })).toHaveAttribute("href", "/admin");
    expect(screen.getByRole("link", { name: "填写记录" })).toHaveAttribute("href", "/admin/assessments");
    expect(screen.getByRole("link", { name: "生成任务" })).toHaveAttribute("href", "/admin/generation-jobs");
    expect(screen.getByRole("link", { name: "成功报告" })).toHaveAttribute("href", "/admin/reports");
    expect(screen.getByRole("link", { name: "审计日志" })).toHaveAttribute("href", "/admin/audit-logs");
  });
});
