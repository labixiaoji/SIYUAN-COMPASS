type ReportBlock =
  | { type: "title"; text: string }
  | {
      type: "section";
      title: string;
      body: Array<
        | { type: "paragraph"; text: string }
        | { type: "subheading"; text: string }
        | { type: "listItem"; index: string; text: string }
        | { type: "listDetail"; text: string }
        | { type: "action"; index: string; text: string }
        | { type: "actionDetail"; text: string }
      >;
    };

function cleanMarkdownText(value: string) {
  return value
    .replace(/^#{1,6}\s*/, "")
    .replace(/^[-*+]\s+/, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/^>\s*/, "")
    .trim();
}

function stripInlineMarkdown(value: string) {
  return cleanMarkdownText(value)
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/__([^_]+)__/g, "$1")
    .replace(/_([^_]+)_/g, "$1");
}

function renderTitle(value: string) {
  const text = cleanMarkdownText(value);
  const parts = text.split(/(\*\*[^*]+\*\*|__[^_]+__)/g).filter(Boolean);

  if (parts.length > 1) {
    return parts.map((part, index) => {
      const boldMatch = part.match(/^(\*\*|__)(.+)(\*\*|__)$/);
      if (boldMatch) {
        return <strong key={`${part}-${index}`}>{boldMatch[2]}</strong>;
      }
      return <span key={`${part}-${index}`}>{part.replace(/\*([^*]+)\*/g, "$1").replace(/_([^_]+)_/g, "$1")}</span>;
    });
  }

  return stripInlineMarkdown(text);
}

function renderBodyText(value: string) {
  const text = cleanMarkdownText(value);
  const boldLeadMatch = text.match(/^(\*\*|__)(.+?)(\*\*|__)(.*)$/);
  if (boldLeadMatch) {
    return (
      <>
        <strong>{stripInlineMarkdown(boldLeadMatch[2])}</strong>
        <span>{stripInlineMarkdown(boldLeadMatch[4]).trimStart()}</span>
      </>
    );
  }

  const labelMatch = stripInlineMarkdown(text).match(/^([^：:。！？!?，,；;]{2,28}[：:])(.+)$/);
  if (labelMatch) {
    return (
      <>
        <strong>{labelMatch[1]}</strong>
        <span>{labelMatch[2].trimStart()}</span>
      </>
    );
  }

  return stripInlineMarkdown(text);
}

function isActionSection(title: string) {
  return title.includes("接下来6个月");
}

function isStrengthsAndRisksSection(title: string) {
  return title.includes("核心优势与风险短板") || title.includes("优势，以及还可以继续积累");
}

function hasParentSinceLastSubheading(
  body: Extract<ReportBlock, { type: "section" }>["body"],
  parentType: "listItem" | "action"
) {
  for (let index = body.length - 1; index >= 0; index -= 1) {
    if (body[index].type === "subheading") return false;
    if (body[index].type === parentType) return true;
  }
  return false;
}

function isActionDetail(value: string) {
  const text = stripInlineMarkdown(value);
  return /^(可以从这些步骤开始|这一步为什么重要|做到什么算完成|适合什么时候做|它和未来方向的关系|做完后重点看看|它会帮助你判断|做什么|为什么做|对\s*Plan\s*A\s*的帮助|如何为\s*Plan\s*B\s*预留后手|为\s*Plan\s*B\s*预留后手|如何验证\s*Plan\s*C|对\s*Plan\s*C\s*的帮助|验证路径|完成标准|建议时间)[：:]/i.test(text);
}

function isReportListDetail(value: string) {
  const text = stripInlineMarkdown(value);
  return /^(你已经做过的事|目前能看到的线索|目前需要留意的是|以后可能会用在|如果暂时不处理|可以先做|眼下可以补上的|可以先从哪一步开始|什么时候值得重新想一想|具体来说|你已经提供的事实|目前可见的线索|目前能看到的信号|它对未来的意义|如果不验证，可能会|接下来可以这样确认|现在还差什么|先做一个什么验证|什么时候重新判断|依据|证据状态|影响|验证或改善|路径方向|适配依据|主要风险|下一步验证|切换条件)[：:]/.test(text);
}

function isChineseSectionHeading(value: string) {
  return /^[一二三四五六七八九十]+[、.．]\s*\S+/.test(stripInlineMarkdown(value));
}

function isSubheading(value: string) {
  return /^[^：:。！？!?，,；;]{2,28}[：:]$/.test(stripInlineMarkdown(value));
}

function isPlanHeading(value: string) {
  return /^Plan\s*[ABC]\s*[：:]/i.test(stripInlineMarkdown(value));
}

function parseReport(content: string): ReportBlock[] {
  const blocks: ReportBlock[] = [];
  let currentSection: Extract<ReportBlock, { type: "section" }> | null = null;

  for (const rawLine of content.split("\n")) {
    const isNestedBullet = /^\s{2,}[-*+]\s+/.test(rawLine);
    const line = rawLine.trim();
    if (!line) continue;
    if (/^(?:\*{3,}|-{3,}|_{3,})$/.test(line)) continue;

    if (/^#\s+/.test(line)) {
      blocks.push({ type: "title", text: cleanMarkdownText(line) });
      currentSection = null;
      continue;
    }

    if (/^##\s+/.test(line)) {
      currentSection = { type: "section", title: cleanMarkdownText(line), body: [] };
      blocks.push(currentSection);
      continue;
    }

    if (/^(?:#{1,6}\s*)?(?:\*\*|__)?安全提醒(?:\*\*|__)?[：:]?$/.test(line)) {
      currentSection = { type: "section", title: "安全提醒", body: [] };
      blocks.push(currentSection);
      continue;
    }

    if (/^#{3,6}\s+/.test(line)) {
      if (!currentSection) {
        currentSection = { type: "section", title: "报告摘要", body: [] };
        blocks.push(currentSection);
      }
      currentSection.body.push({ type: "subheading", text: cleanMarkdownText(line) });
      continue;
    }

    if (isChineseSectionHeading(line)) {
      currentSection = { type: "section", title: stripInlineMarkdown(line), body: [] };
      blocks.push(currentSection);
      continue;
    }

    if (!currentSection) {
      currentSection = { type: "section", title: "报告摘要", body: [] };
      blocks.push(currentSection);
    }

    if (isSubheading(line) || isPlanHeading(line)) {
      currentSection.body.push({ type: "subheading", text: cleanMarkdownText(line) });
      continue;
    }

    const actionMatch = line.match(/^(\d+)\.\s*(.+)$/);
    if (actionMatch) {
      const text = cleanMarkdownText(actionMatch[2]);
      const type = isActionSection(currentSection.title)
        ? (isActionDetail(text) ? "actionDetail" : "action")
        : "listItem";
      currentSection.body.push({
        type,
        ...(type === "actionDetail" ? {} : { index: actionMatch[1] }),
        text
      } as Extract<ReportBlock, { type: "section" }>["body"][number]);
    } else if (/^[-*+]\s+/.test(line)) {
      const text = cleanMarkdownText(line);
      const followsAction = hasParentSinceLastSubheading(currentSection.body, "action");
      const followsAnalysisItem = hasParentSinceLastSubheading(currentSection.body, "listItem");
      const type = isActionSection(currentSection.title)
        ? (isNestedBullet || isActionDetail(text) || followsAction ? "actionDetail" : "action")
        : (
            isNestedBullet
            || isReportListDetail(text)
            || (isStrengthsAndRisksSection(currentSection.title) && followsAnalysisItem)
              ? "listDetail"
              : "listItem"
          );
      currentSection.body.push({
        type,
        ...(type === "actionDetail" || type === "listDetail"
          ? {}
          : { index: String(currentSection.body.filter((item) => item.type === type).length + 1) }),
        text
      } as Extract<ReportBlock, { type: "section" }>["body"][number]);
    } else {
      currentSection.body.push({ type: "paragraph", text: cleanMarkdownText(line) });
    }
  }

  return blocks;
}

export function ReportRenderer({ content }: { content: string }) {
  const blocks = parseReport(content);
  const sections = blocks.filter((block): block is Extract<ReportBlock, { type: "section" }> => block.type === "section");

  return (
    <article className="report-reader">
      {sections.map((section) => {
        let listItemCount = 0;
        let actionCount = 0;

        return (
          <section className="report-section" key={section.title}>
            <h2>{renderTitle(section.title)}</h2>
            {section.body.map((item, index) => {
              if (item.type === "subheading") {
                listItemCount = 0;
                return <h3 key={`${section.title}-h-${index}`}>{renderTitle(item.text)}</h3>;
              }

              if (item.type === "paragraph") {
                return <p key={`${section.title}-p-${index}`}>{renderBodyText(item.text)}</p>;
              }

              if (item.type === "listItem") {
                listItemCount += 1;
                return (
                  <div className="report-list-item" key={`${section.title}-l-${index}`}>
                    <span className="report-list-index">{listItemCount}</span>
                    <span>{renderBodyText(item.text)}</span>
                  </div>
                );
              }

              if (item.type === "listDetail") {
                return (
                  <div className="report-list-detail" key={`${section.title}-ld-${index}`}>
                    <span className="report-list-detail-dot" />
                    <span>{renderBodyText(item.text)}</span>
                  </div>
                );
              }

              if (item.type === "actionDetail") {
                return (
                  <div className="action-detail" key={`${section.title}-d-${index}`}>
                    <span className="action-detail-dot" />
                    <span>{renderBodyText(item.text)}</span>
                  </div>
                );
              }

              actionCount += 1;
              return (
                <div className="action-card" key={`${section.title}-a-${index}`}>
                  <span className="action-index">{actionCount}</span>
                  <span>{renderBodyText(item.text)}</span>
                </div>
              );
            })}
          </section>
        );
      })}
    </article>
  );
}
