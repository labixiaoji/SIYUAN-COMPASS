import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { AdminNavigation } from "./AdminNavigation";

describe("AdminNavigation", () => {
  it("提供总览、用户、填写记录、报告和修改记录入口", () => {
    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <AdminNavigation />
      </MemoryRouter>
    );

    expect(screen.getByRole("link", { name: "总览" })).toHaveAttribute("href", "/admin");
    expect(screen.getByRole("link", { name: "用户管理" })).toHaveAttribute("href", "/admin/users");
    expect(screen.getByRole("link", { name: "填写记录" })).toHaveAttribute("href", "/admin/assessments");
    expect(screen.getByRole("link", { name: "已生成报告" })).toHaveAttribute("href", "/admin/reports");
    expect(screen.getByRole("link", { name: "报告修改记录" })).toHaveAttribute("href", "/admin/audit-logs");
    expect(screen.queryByRole("link", { name: "生成任务" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "成功报告" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "审计日志" })).not.toBeInTheDocument();
  });
});
