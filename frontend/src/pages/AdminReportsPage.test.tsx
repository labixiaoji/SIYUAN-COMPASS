import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fetchAdminRecords } from "../api/admin";
import type { AdminRecord } from "../types/report";
import { AdminReportsPage } from "./AdminReportsPage";

vi.mock("../api/admin", () => ({
  fetchAdminRecords: vi.fn()
}));

function makeRecord(overrides: Partial<AdminRecord> = {}): AdminRecord {
  return {
    report: {
      id: "report-1",
      userId: "user-1",
      responseId: "response-1",
      profileId: "profile-1",
      title: "我的生涯蓝图",
      content: "这是一份报告正文。",
      wordCount: 12,
      generationStatus: "success",
      qualityStatus: "warning",
      modelName: "deepseek",
      promptVersion: "career-blueprint-v1.2.0",
      retryCount: 0,
      createdAt: "2026-09-03T08:00:00Z",
      updatedAt: "2026-09-03T08:00:00Z",
      inputSnapshot: {}
    },
    student: {
      id: "user-1",
      username: "student-1",
      displayName: "林同学",
      school: "计算机学院"
    },
    assessment: {
      educationStage: "本科",
      grade: "大三",
      collegeMajor: "软件工程",
      submittedAt: "2026-09-03T08:00:00Z"
    },
    feedbacks: [],
    ...overrides
  };
}

function renderPage() {
  return render(
    <MemoryRouter>
      <AdminReportsPage />
    </MemoryRouter>
  );
}

describe("AdminReportsPage", () => {
  beforeEach(() => {
    vi.mocked(fetchAdminRecords).mockResolvedValue({
      records: [
        makeRecord(),
        makeRecord({
          report: {
            ...makeRecord().report,
            id: "report-2",
            title: "另一份生涯蓝图",
            qualityStatus: "passed"
          },
          student: {
            id: "user-2",
            username: "student-2",
            displayName: "周同学",
            school: "马克思主义学院"
          },
          assessment: {
            educationStage: "硕士",
            grade: "研一",
            collegeMajor: "马克思主义理论",
            submittedAt: "2026-09-03T09:00:00Z"
          }
        })
      ]
    });
  });

  it("恢复宽版报告卡片并展示问卷、状态和反馈区域", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: "我的生涯蓝图", level: 3 })).toBeInTheDocument();
    expect(screen.getAllByText("问卷内容")).toHaveLength(2);
    expect(screen.getAllByText("报告状态")).toHaveLength(3);
    expect(screen.getAllByText("反馈记录")).toHaveLength(2);
    expect(screen.getByText("学院：计算机学院")).toBeInTheDocument();
  });

  it("支持姓名、学院和专业模糊搜索，以及报告状态和年级筛选", async () => {
    renderPage();
    await screen.findByRole("heading", { name: "我的生涯蓝图", level: 3 });

    const keyword = screen.getByPlaceholderText("输入姓名、学院或专业关键词");
    fireEvent.change(keyword, { target: { value: "马克思" } });
    expect(screen.queryByRole("heading", { name: "我的生涯蓝图", level: 3 })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "另一份生涯蓝图", level: 3 })).toBeInTheDocument();

    fireEvent.change(keyword, { target: { value: "" } });
    fireEvent.change(screen.getByLabelText("报告状态"), { target: { value: "warning" } });
    expect(screen.getByRole("heading", { name: "我的生涯蓝图", level: 3 })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "另一份生涯蓝图", level: 3 })).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("年级"), { target: { value: "研一" } });
    expect(screen.queryByRole("heading", { name: "我的生涯蓝图", level: 3 })).not.toBeInTheDocument();
  });
});
