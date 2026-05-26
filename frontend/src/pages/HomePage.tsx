import { Link } from "react-router-dom";

export function HomePage() {
  return (
    <main className="shell hero">
      <section>
        <h1>交大学生生涯规划智能体</h1>
        <p className="lead">
          用8-12分钟完成首次填写，生成一份个性化《我的生涯蓝图》。系统会帮你梳理未来愿景、当前优势、路径风险和接下来6个月的行动建议。
        </p>
        <div className="actions" style={{ justifyContent: "flex-start" }}>
          <Link className="button" to="/assessment">开始填写</Link>
        </div>
      </section>
      <aside className="panel">
        <h2>第一阶段闭环</h2>
        <p className="hint">首次填写、画像提取、状态判断、报告生成和反馈评分已经串成一条最小可用流程。</p>
        <div className="stat-grid">
          <div className="stat"><strong>24</strong><span>核心问题</span></div>
          <div className="stat"><strong>6</strong><span>生涯状态</span></div>
          <div className="stat"><strong>7+1</strong><span>报告结构</span></div>
          <div className="stat"><strong>4</strong><span>反馈评分</span></div>
        </div>
      </aside>
    </main>
  );
}
