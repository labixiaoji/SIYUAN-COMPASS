import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fetchAdminAssessments } from "../api/admin";
import { AdminAssessmentsPage } from "./AdminAssessmentsPage";

vi.mock("../api/admin", () => ({
  fetchAdminAssessments: vi.fn()
}));

describe("AdminAssessmentsPage", () => {
  beforeEach(() => {
    vi.mocked(fetchAdminAssessments).mockResolvedValue({ total: 0, items: [] });
  });

  it("从地址参数读取账号并自动搜索填写记录", async () => {
    render(
      <MemoryRouter initialEntries={["/admin/assessments?keyword=test002"]}>
        <AdminAssessmentsPage />
      </MemoryRouter>
    );

    expect(screen.getByPlaceholderText("姓名、账号、专业或记录编号")).toHaveValue("test002");
    await waitFor(() => {
      expect(fetchAdminAssessments).toHaveBeenCalledWith({
        keyword: "test002",
        status: "all",
        limit: 20,
        offset: 0
      });
    });
  });

  it("切换状态时保留账号搜索条件", async () => {
    render(
      <MemoryRouter initialEntries={["/admin/assessments?keyword=test002"]}>
        <AdminAssessmentsPage />
      </MemoryRouter>
    );

    await waitFor(() => expect(fetchAdminAssessments).toHaveBeenCalled());
    fireEvent.change(screen.getByLabelText("记录状态"), { target: { value: "failed" } });

    await waitFor(() => {
      expect(fetchAdminAssessments).toHaveBeenLastCalledWith({
        keyword: "test002",
        status: "failed",
        limit: 20,
        offset: 0
      });
    });
  });
});
