type ReportBlock =
  | { type: "title"; text: string }
  | {
      type: "section";
      title: string;
      body: Array<
        | { type: "paragraph"; text: string }
        | { type: "subheading"; text: string }
        | { type: "listItem"; index: string; text: string }
        | { type: "action"; index: string; text: string }
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
  return title.includes("接下来6个月建议");
}

function isChineseSectionHeading(value: string) {
  return /^[一二三四五六七八九十]+[、.．]\s*\S+/.test(stripInlineMarkdown(value));
}

function isSubheading(value: string) {
  return /^[^：:。！？!?，,；;]{2,28}[：:]$/.test(stripInlineMarkdown(value));
}

function parseReport(content: string): ReportBlock[] {
  const blocks: ReportBlock[] = [];
  let currentSection: Extract<ReportBlock, { type: "section" }> | null = null;

  for (const rawLine of content.split("\n")) {
    const line = rawLine.trim();
    if (!line) continue;

    if (/^#\s+/.test(line)) {
      blocks.push({ type: "title", text: cleanMarkdownText(line) });
      currentSection = null;
      continue;
    }

    if (/^#{2,6}\s+/.test(line)) {
      currentSection = { type: "section", title: cleanMarkdownText(line), body: [] };
      blocks.push(currentSection);
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

    if (isSubheading(line)) {
      currentSection.body.push({ type: "subheading", text: cleanMarkdownText(line) });
      continue;
    }

    const actionMatch = line.match(/^(\d+)\.\s*(.+)$/);
    if (actionMatch) {
      currentSection.body.push({
        type: isActionSection(currentSection.title) ? "action" : "listItem",
        index: actionMatch[1],
        text: cleanMarkdownText(actionMatch[2])
      });
    } else if (/^[-*+]\s+/.test(line)) {
      const type = isActionSection(currentSection.title) ? "action" : "listItem";
      currentSection.body.push({
        type,
        index: String(currentSection.body.filter((item) => item.type === type).length + 1),
        text: cleanMarkdownText(line)
      });
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
