import json
import unittest

from pydantic import ValidationError

from app.schemas.report import CareerBlueprintDraft
from app.services.report_generator import _parse_report_json
from app.services.report_quality_check import check_report_quality
from app.services.report_renderer import render_report_markdown


def make_draft_payload() -> dict:
    return {
        "portrait": {
            "fiveYearPortrait": "五年后的一个普通工作日，你可能生活在自己喜欢并且机会相对集中的城市。早上走进一支规模不算太大的技术团队，工作不只是完成分配下来的任务，也包括理解真实需求、整理信息和推动不同角色形成共识。你会花一部分时间阅读访谈记录和业务数据，一部分时间与产品、设计或技术同事讨论方案，再把复杂信息整理成清楚的结论。经过几个完整项目，你已经能够独立负责一块工作，也知道自己更喜欢靠近用户、项目协调还是专业分析。下班后的时间仍然属于自己的生活，你可以继续一项愿意长期投入的兴趣，也能给家人和朋友留下稳定的相处时间。工作带来成长感，却不会占据生活的全部。",
            "tenYearPortrait": "到了十年左右，你可能已经在技术与真实需求之间形成了自己的专业位置。你对行业变化不再只是被动跟随，而是能够凭借积累的项目经验判断哪些问题值得投入，也能带着更年轻的伙伴完成从研究、分析到落地的全过程。职业上的稳定来自能够迁移的能力和可信的作品，而不是被固定在某一个岗位名称里。生活方面，你对适合自己的城市、居住方式和工作节奏有了更清楚的选择，重要关系、个人兴趣和职业投入之间也形成了更可持续的安排。回头看大学阶段的困惑，它们并没有靠一次决定全部消失，而是在一次次真实经历中慢慢变得清晰；你最终得到的是一套更了解自己、也更能应对变化的生活方式。",
        },
        "strengthsAndRisks": {
            "strengths": [
                {
                    "title": "持续学习",
                    "evidenceStatus": "verified",
                    "studentNarrative": "你已经在课程项目里表现出持续补充知识并推进任务的能力，这比一次自我评价更能说明问题。",
                    "futureRelevance": "这会帮助你适应需要不断更新知识的技术和产品工作。",
                    "evidence": ["课程项目能够按期完成"],
                },
                {
                    "title": "结构化分析",
                    "evidenceStatus": "potential",
                    "studentNarrative": "你习惯先拆解问题再行动，这可能成为优势，但还需要在更复杂的真实任务里继续确认。",
                    "futureRelevance": "如果得到更多项目反馈，它会成为连接技术、需求和协作的重要能力。",
                    "evidence": ["解决问题时会主动查资料并比较方案"],
                },
            ],
            "risks": [
                {
                    "title": "岗位信息不足",
                    "evidenceStatus": "risk",
                    "studentNarrative": "你对目标岗位的判断目前主要来自二手信息，因此期待中的工作和真实日常可能存在差距。",
                    "futureRelevance": "如果长期缺少一手信息，后续投入可能建立在想象之上。",
                    "evidence": ["尚未进行岗位访谈"],
                    "validation": "完成两次从业者访谈并整理共同结论。",
                },
                {
                    "title": "行动证据偏少",
                    "evidenceStatus": "risk",
                    "studentNarrative": "目前能够比较不同方向的真实任务还不够多，兴趣和能力之间的关系尚未被充分验证。",
                    "futureRelevance": "这会让你很难判断自己是不喜欢方向，还是暂时不熟悉任务。",
                    "evidence": ["暂时没有相关实习或独立作品"],
                    "validation": "完成一个两周小项目并获取外部反馈。",
                },
            ],
        },
        "diagnosis": {
            "currentConfusion": "当前最主要的困惑是不确定未来适合什么方向。",
            "underlyingProblem": "真正的问题是缺少岗位事实和真实任务反馈，暂时无法区分不了解、没兴趣和能力尚未形成。",
            "pathRelationship": "Plan A可以作为目前最先了解的方向，Plan B保留已有专业基础带来的选择空间，Plan C则用一次成本可控的体验打开新的可能。现阶段可以把主要精力放在Plan A，同时维持Plan B需要的基础，并为Plan C留出一次短期体验。",
            "plans": [
                {
                    "id": "A",
                    "title": "连接技术与真实需求的产品方向",
                    "futureScene": "如果这条路逐渐被验证，未来几年的工作会包含需求分析、跨团队沟通和项目推进。",
                    "whyItFitsYou": "它与你已经表现出的任务拆解和沟通线索有关，也能回应你对成长空间的重视。",
                    "currentGap": "目前最缺少的是真实岗位信息和一份能够接受外部评价的作品。",
                    "firstExperiment": "先完成两次岗位访谈，再做一个小型需求分析作品。",
                    "decisionSignal": "如果你喜欢核心工作过程且外部反馈稳定，可以继续投入；否则重新比较另外两条路径。",
                },
                {
                    "id": "B",
                    "title": "沿专业基础继续积累的技术方向",
                    "futureScene": "这条路会让你在熟悉的专业基础上继续积累，并通过真实技术任务逐步形成可迁移能力。",
                    "whyItFitsYou": "已有课程基础能够降低起步成本，也适合作为主攻方向尚未验证时的稳定备选。",
                    "currentGap": "需要确认你喜欢的是解决技术问题本身，还是因为这条路更加熟悉。",
                    "firstExperiment": "选择一项完整专业任务，完成后请教师或从业者评价过程和结果。",
                    "decisionSignal": "如果投入感和任务表现持续高于主攻方向，可以提高这条路径的优先级。",
                },
                {
                    "id": "C",
                    "title": "数据分析与公益项目结合的探索方向",
                    "futureScene": "这是一条低成本探索路径，可以让你在真实公益议题中使用分析能力并观察价值感来源。",
                    "whyItFitsYou": "它能够同时验证你的分析倾向和助人价值是否值得进入长期选择，也能帮助你判断自己是否喜欢把能力用在具体公共议题上。",
                    "currentGap": "目前没有直接项目证据，因此只能作为探索方向。",
                    "firstExperiment": "参加一次短期公益数据项目，记录喜欢和消耗精力的具体任务。",
                    "decisionSignal": "只有获得明确正向反馈并愿意持续投入时，才进入下一轮探索。",
                },
            ],
        },
        "sixMonthActions": [
            {
                "title": "完成岗位访谈",
                "purpose": "补齐目标岗位的一手信息。",
                "steps": ["联系两名从业者", "记录工作内容、能力要求和常见困难"],
                "completionCriteria": "形成一页访谈对照表并列出三条新发现。",
                "deadline": "第1个月",
                "validatesPlans": ["A", "B"],
                "pathConnection": "这次访谈主要帮助你了解Plan A的真实工作内容，也能比较Plan B相关岗位在职责和进入方式上的差异。",
                "reflectionSignal": "重点看看哪类工作内容更能调动你的兴趣，以及两条方向的实际门槛是否符合原来的判断。",
            },
            {
                "title": "完成小型项目",
                "purpose": "验证兴趣、执行力和实际能力差距。",
                "steps": ["选择一个两周任务", "完成作品并获取一次外部评价"],
                "completionCriteria": "形成可展示成果和一次书面复盘。",
                "deadline": "第2—3个月",
                "validatesPlans": ["A"],
                "pathConnection": "这份作品直接对应Plan A需要的用户研究和产品分析过程，可以让你体验这条方向最核心的任务。",
                "reflectionSignal": "重点看看你是否喜欢反复理解用户、整理信息和修改结论，以及外部反馈是否认可作品质量。",
            },
            {
                "title": "进行路径复盘",
                "purpose": "根据事实决定继续投入或切换。",
                "steps": ["比较三条路径的新证据", "记录保留、放弃和继续验证的理由"],
                "completionCriteria": "完成路径决策表并确定下一阶段主线。",
                "deadline": "第6个月",
                "validatesPlans": ["A", "B", "C"],
                "pathConnection": "这次复盘把Plan A、Plan B和Plan C放在同一组事实下比较，帮助你重新安排三条方向的先后顺序。",
                "reflectionSignal": "重点看看哪条方向同时获得了真实体验、外部反馈和持续投入意愿，哪条仍主要停留在想象中。",
            },
        ],
        "reviewQuestions": [
            "你通过访谈获得了哪些过去不知道、并且会影响选择的岗位事实？",
            "哪个真实任务让你更愿意继续投入，具体是任务的哪个部分？",
            "教师或从业者的外部评价支持了哪些优势判断，又否定了哪些假设？",
            "最主要的困惑发生了什么变化，还有哪一项信息没有得到验证？",
            "根据半年内获得的新证据，Plan A、Plan B、Plan C的顺序是否需要调整？",
        ],
        "longTermQuestion": {
            "context": "路径选择不需要一次完成，关键是持续用行动换取更可靠的证据。当愿景、兴趣和现实条件暂时不能完全一致时，能够区分长期方向和当前可执行步骤，会比反复寻找一个确定答案更有帮助。",
            "question": "未来面对重要选择时，你愿意用什么最小行动检验自己的判断？",
        },
    }


class StructuredReportGenerationTest(unittest.TestCase):
    def test_draft_requires_three_distinct_plan_ids(self):
        payload = make_draft_payload()
        payload["diagnosis"]["plans"][2]["id"] = "B"

        with self.assertRaises(ValidationError):
            CareerBlueprintDraft.model_validate(payload)

    def test_draft_requires_three_to_five_actions(self):
        payload = make_draft_payload()
        payload["sixMonthActions"] = payload["sixMonthActions"][:2]

        with self.assertRaises(ValidationError):
            CareerBlueprintDraft.model_validate(payload)

    def test_draft_rejects_empty_evidence_items(self):
        payload = make_draft_payload()
        payload["strengthsAndRisks"]["strengths"][0]["evidence"] = ["   "]

        with self.assertRaises(ValidationError):
            CareerBlueprintDraft.model_validate(payload)

    def test_draft_keeps_potential_strengths_distinct_from_verified_strengths(self):
        payload = make_draft_payload()
        payload["strengthsAndRisks"]["strengths"][0]["evidenceStatus"] = "risk"

        with self.assertRaises(ValidationError):
            CareerBlueprintDraft.model_validate(payload)

    def test_action_connection_does_not_need_to_repeat_internal_plan_labels(self):
        payload = make_draft_payload()
        payload["sixMonthActions"][0]["pathConnection"] = "这次访谈可以同时比较主攻方向和专业备选方向的真实工作内容。"

        draft = CareerBlueprintDraft.model_validate(payload)
        markdown = render_report_markdown(draft)

        self.assertIn("它和未来方向的关系（Plan A、Plan B）", markdown)

    def test_six_month_actions_can_focus_on_current_priority_paths(self):
        payload = make_draft_payload()
        payload["sixMonthActions"][2]["validatesPlans"] = ["A", "B"]
        payload["sixMonthActions"][2]["pathConnection"] = "这次复盘会把主攻方向和专业备选方向放在同一组事实下比较。"

        draft = CareerBlueprintDraft.model_validate(payload)

        self.assertEqual(draft.sixMonthActions[2].validatesPlans, ["A", "B"])

    def test_draft_accepts_four_relevant_evidence_items(self):
        payload = make_draft_payload()
        payload["strengthsAndRisks"]["strengths"][0]["evidence"] = [
            "课程项目按期完成",
            "主动整理资料",
            "小组汇报表达清楚",
            "会复盘项目过程",
        ]

        draft = CareerBlueprintDraft.model_validate(payload)

        self.assertEqual(len(draft.strengthsAndRisks.strengths[0].evidence), 4)

    def test_risk_item_can_omit_repeated_action_advice(self):
        payload = make_draft_payload()
        payload["strengthsAndRisks"]["risks"][0]["validation"] = ""

        markdown = render_report_markdown(CareerBlueprintDraft.model_validate(payload))

        self.assertEqual(markdown.count("  - 可以先做："), 1)

    def test_parser_accepts_fenced_json_and_renderer_creates_canonical_markdown(self):
        payload = make_draft_payload()
        raw = f"```json\n{json.dumps(payload, ensure_ascii=False)}\n```"

        draft = _parse_report_json(raw)
        markdown = render_report_markdown(draft)
        quality = check_report_quality(markdown)

        self.assertIn("## 二、你的优势，以及还可以继续积累的地方", markdown)
        self.assertIn("## 三、从现在走向未来，可以怎样选择", markdown)
        self.assertIn("五年后的一个普通工作日", markdown)
        portrait = markdown.split("## 一、你5—10年后的人生画像", 1)[1].split("## 二、", 1)[0]
        self.assertNotIn("###", portrait)
        self.assertNotIn("接下来", portrait)
        self.assertIn("### Plan A：连接技术与真实需求的产品方向（主攻路径）", markdown)
        self.assertIn("### Plan B：沿专业基础继续积累的技术方向（备选路径）", markdown)
        self.assertIn("### Plan C：数据分析与公益项目结合的探索方向（探索路径）", markdown)
        self.assertNotIn("证据状态：", markdown)
        intro_position = markdown.index("### 接下来，看看三种可能的方向")
        plan_a_position = markdown.index("### Plan A：")
        plan_c_position = markdown.index("### Plan C：")
        arrangement_position = markdown.index("### 把三条方向放在一起，可以怎么安排？")
        self.assertLess(intro_position, plan_a_position)
        self.assertLess(plan_c_position, arrangement_position)
        self.assertIn("\n  - 你已经在课程项目里表现出", markdown)
        self.assertIn("\n  - 你已经做过的事：", markdown)
        self.assertIn("\n  - 可以从这些步骤开始：", markdown)
        self.assertIn(
            "- 它和未来方向的关系（Plan A、Plan B）：这次访谈主要帮助你了解Plan A",
            markdown,
        )
        self.assertIn("- 做完后重点看看：重点看看哪类工作内容", markdown)
        self.assertFalse(any("缺少模块" in item for item in quality["warnings"]))
        self.assertFalse(any("缺少关键内容" in item for item in quality["warnings"]))
        self.assertFalse(any("行动项格式或数量异常" in item for item in quality["warnings"]))

    def test_renderer_collapses_model_newlines_so_content_cannot_create_headings(self):
        payload = make_draft_payload()
        payload["diagnosis"]["plans"][0]["futureScene"] = "技术产品方向的真实工作日常包含需求分析和团队协作，需要在多方反馈中持续推进。\n## 伪造模块"

        markdown = render_report_markdown(CareerBlueprintDraft.model_validate(payload))

        self.assertNotIn("\n## 伪造模块", markdown)


if __name__ == "__main__":
    unittest.main()
