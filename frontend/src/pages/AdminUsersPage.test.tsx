import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fetchAdminUsers } from "../api/admin";
import { AdminUsersPage } from "./AdminUsersPage";

vi.mock("../api/admin", () => ({
  fetchAdminUsers: vi.fn()
}));

describe("AdminUsersPage", () => {
  beforeEach(() => {
    vi.mocked(fetchAdminUsers).mockResolvedValue({
      summary: { total: 52, studentCount: 51, adminCount: 1 },
      total: 2,
      items: [
        {
          id: "user-1",
          username: "test002",
          displayName: "测试学生 002",
          role: "student",
          createdAt: "2026-09-09T01:00:00Z",
          updatedAt: "2026-09-09T02:00:00Z",
          lastActivityAt: "2026-09-09T03:00:00Z",
          assessmentCount: 3,
          generationJobCount: 4,
          reportCount: 2
        },
        {
          id: "admin-1",
          username: "admin",
          displayName: "系统管理员",
          role: "admin",
          createdAt: "2026-09-01T01:00:00Z",
          updatedAt: "2026-09-09T02:00:00Z",
          lastActivityAt: "2026-09-09T02:00:00Z",
          assessmentCount: 0,
          generationJobCount: 0,
          reportCount: 0
        }
      ]
    });
  });

  it("展示用户总数、角色统计和账号使用数据", async () => {
    render(<MemoryRouter><AdminUsersPage /></MemoryRouter>);

    expect(await screen.findByText("测试学生 002")).toBeInTheDocument();
    expect(screen.getByText("52")).toBeInTheDocument();
    expect(screen.getByText("51")).toBeInTheDocument();
    expect(screen.getAllByText("管理员").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "测试学生 002" })).toHaveAttribute(
      "href",
      "/admin/assessments?keyword=test002"
    );
    expect(screen.getByText("test002")).toBeInTheDocument();
    expect(screen.getByText("user-1")).toBeInTheDocument();
  });

  it("修改搜索和角色时重新从第一页查询", async () => {
    render(<MemoryRouter><AdminUsersPage /></MemoryRouter>);
    await screen.findByText("测试学生 002");

    fireEvent.change(screen.getByPlaceholderText("账号、昵称或用户 ID"), { target: { value: "test002" } });
    fireEvent.change(screen.getByLabelText("用户角色"), { target: { value: "student" } });

    await waitFor(() => {
      expect(fetchAdminUsers).toHaveBeenLastCalledWith({
        keyword: "test002",
        role: "student",
        limit: 20,
        offset: 0
      });
    });
  });
});
