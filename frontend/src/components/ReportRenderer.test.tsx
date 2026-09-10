import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ReportRenderer } from "./ReportRenderer";


describe("ReportRenderer", () => {
  it("把每项能力作为一级编号并把证据和影响显示为下级详情", () => {
    const content = `
## 二、你的核心优势与风险短板
### 核心优势
1. **逻辑分析与任务拆解能力**
- 你能够拆解任务并完成汇报。
- 你已经做过的事：课程项目和组员反馈
- 以后可能会用在：处理结构复杂的工作
2. **主动学习能力**
- 你会主动学习新工具。
- 目前能看到的线索：持续整理项目资料
- 以后可能会用在：适应需要更新知识的领域
`.trim();

    const { container } = render(<ReportRenderer content={content} />);

    expect(container.querySelectorAll(".report-list-item")).toHaveLength(2);
    expect(container.querySelectorAll(".report-list-detail")).toHaveLength(6);
  });

  it("能力下方的无序列表即使更换文案也保持为下级详情", () => {
    const content = `
## 二、你的核心优势与风险短板
### 核心优势
1. **任务拆解能力**
- 这项能力怎样表现：能够把复杂任务拆成连续步骤
- 未来可以怎样使用：适合处理跨团队项目
2. **主动学习习惯**
- 下一步可以观察：能否把学习成果转成作品
`.trim();

    const { container } = render(<ReportRenderer content={content} />);

    expect(container.querySelectorAll(".report-list-item")).toHaveLength(2);
    expect(container.querySelectorAll(".report-list-detail")).toHaveLength(3);
  });

  it("把学生行动的说明显示为所属行动的下级详情", () => {
    const content = `
## 四、接下来6个月，你可以做的3—5件事
1. **完成岗位访谈**
- 先从哪里开始：联系两名从业者
- 这一步为什么重要：补齐岗位事实
- 做到什么算完成：形成访谈对照表
- 适合什么时候做：第1个月
- 它和未来方向的关系：帮助了解Plan A的工作内容，并比较Plan B的进入方式
- 做完后重点看看：哪类工作内容更符合自己的兴趣
## 五、半年后我会问你这些问题
1. 你获得了哪些岗位事实？
`.trim();

    const { container } = render(<ReportRenderer content={content} />);

    expect(container.querySelectorAll(".action-card")).toHaveLength(1);
    expect(container.querySelectorAll(".action-detail")).toHaveLength(6);
  });
});
