import unittest

from app.services.report_quality_check import check_report_quality, extract_action_items


def make_report(extra_body: str = "", include_plan_c: bool = True) -> str:
    portrait = extra_body or "五年后的生活包含喜欢的城市、日常工作和稳定节奏，到了十年左右，职业角色与生活安排会逐渐清晰。" * 14
    strengths = "课程项目与持续准备提供了一些行为证据，但能力自评仍需通过真实任务验证；当前主要风险是信息不足和行动节奏不稳定。" * 10
    plan_a = "围绕当前最明确的目标建立主攻路径。下一步完成岗位访谈和一个真实项目，并以项目反馈作为继续投入或切换的条件。" * 7
    plan_b = "保留与专业基础相关的备选路径。下一步核对课程与岗位要求，通过短期实习验证兴趣，并在证据不足时降低投入。" * 7
    plan_c = (
        "### Plan C：系统建议路径\n"
        + "探索跨专业的低成本验证方向。下一步参加一次校友访谈并完成小型作品，用反馈决定是否进入下一轮行动。" * 7
        + "\n"
        if include_plan_c
        else ""
    )
    actions = f"""1. 完成两次岗位访谈\n- {"记录真实工作内容、能力要求和不确定点。" * 7}\n
2. 完成一个小型项目\n- {"用可展示成果验证兴趣和执行能力。" * 7}\n
3. 更新路径决策表\n- {"对照证据、风险和切换条件做阶段复盘。" * 7}\n"""
    return f"""
# 我的生涯蓝图
## 一、你5—10年后的人生画像
{portrait}
## 二、你的核心优势与风险短板
{strengths}
## 三、人生愿景与当前路径的匹配度诊断
### 你现在最大的困惑是什么？
不知道未来适合做什么
### 这个困惑背后的真正问题是什么？
需要验证目标岗位和自身能力之间的匹配。当前缺少岗位事实、真实任务体验与可比较的行动证据。{"需要继续基于访谈和项目补充事实。" * 8}
### 接下来可以如何验证？
通过访谈、项目和实习验证，并在固定时间复盘结果。{"每次验证都记录预期、结果、差异和下一步。" * 8}
### Plan A：主攻路径
{plan_a}
### Plan B：备选路径
{plan_b}
{plan_c}
## 四、接下来6个月，你可以做的3—5件事
{actions}
## 五、半年后我会问你这些问题
你是否获得了真实岗位信息？是否完成了能被他人评价的项目？哪些证据支持继续，哪些证据提示切换？{"请用事实而不是感受回答。" * 5}
## 六、一个值得你长期思考的问题
如果不把一次选择看成人生定论，你愿意用什么最小行动去换取下一条可信证据？{"这个问题帮助你把焦虑转化为可验证的探索。" * 4}
## 安全提醒
本报告不是医学诊断、心理诊断或人生终局结论。如持续感到焦虑、低落或无力，应联系学校心理咨询中心；升学就业的具体政策与机会应向学校就业指导中心、教务部门或官方渠道核实。
""".strip()


class ReportQualityCheckTest(unittest.TestCase):
    def test_length_warnings_do_not_fail_report(self):
        content = make_report(extra_body="内容" * 3000)

        quality = check_report_quality(content, expected_confusions=["不知道未来适合做什么"])

        self.assertEqual(quality["status"], "warning")
        self.assertEqual(quality["fatalWarnings"], [])
        self.assertTrue(any("报告长度超过" in item or "模块超过" in item for item in quality["warnings"]))

    def test_missing_required_plan_is_fatal(self):
        content = make_report(include_plan_c=False)

        quality = check_report_quality(content, expected_confusions=["不知道未来适合做什么"])

        self.assertEqual(quality["status"], "failed")
        self.assertTrue(any("Plan C" in item for item in quality["fatalWarnings"]))

    def test_missing_exact_confusion_reference_is_warning(self):
        content = make_report()

        quality = check_report_quality(content, expected_confusions=["纠结就业、读研、出国、读博"])

        self.assertEqual(quality["status"], "warning")
        self.assertEqual(quality["fatalWarnings"], [])
        self.assertIn("缺少当前困惑选项引用", quality["warnings"])

    def test_empty_heading_shell_is_rejected(self):
        content = make_report().replace(strengths := "课程项目与持续准备提供了一些行为证据，但能力自评仍需通过真实任务验证；当前主要风险是信息不足和行动节奏不稳定。" * 10, "内容")

        quality = check_report_quality(content)

        self.assertEqual(quality["status"], "failed")
        self.assertTrue(any("模块内容过少" in item for item in quality["fatalWarnings"]))

    def test_personal_identity_leak_is_rejected(self):
        content = make_report() + "\n学生联系方式：student@example.com"

        quality = check_report_quality(content, prohibited_personal_values=["student@example.com"])

        self.assertEqual(quality["status"], "failed")
        self.assertIn("报告包含不应展示的个人身份信息", quality["fatalWarnings"])

    def test_unknown_contact_detail_is_rejected(self):
        content = make_report() + "\n如需联系请拨打 13800138000"

        quality = check_report_quality(content)

        self.assertEqual(quality["status"], "failed")
        self.assertIn("报告包含疑似联系方式或长数字标识", quality["fatalWarnings"])

    def test_action_numbering_variants_are_recognized(self):
        for marker in (
            "1. 完成岗位访谈",
            "1、完成岗位访谈",
            "（1）完成岗位访谈",
            "(1) 完成岗位访谈",
            "**1.** 完成岗位访谈",
            "行动一：完成岗位访谈",
        ):
            content = "\n".join(
                [
                    marker,
                    marker.replace("1", "2", 1).replace("一", "二", 1),
                    marker.replace("1", "3", 1).replace("一", "三", 1),
                ]
            )
            self.assertEqual(len(extract_action_items(content)), 3, marker)

    def test_action_count_is_a_warning_not_a_fatal_failure(self):
        content = make_report().replace("3. 更新路径决策表", "行动三：更新路径决策表")
        content = content.replace("2. 完成一个小型项目", "（2）完成一个小型项目")

        quality = check_report_quality(content)

        self.assertNotIn("行动项格式或数量异常", quality["fatalWarnings"])

    def test_nested_numbered_steps_are_not_counted_as_top_level_actions(self):
        content = make_report().replace(
            "1. 完成两次岗位访谈\n",
            "1. 完成两次岗位访谈\n  1. 联系访谈对象\n  2. 完成访谈\n  3. 整理纪要\n",
        )

        quality = check_report_quality(content)

        self.assertFalse(any("行动项格式或数量异常" in item for item in quality["warnings"]))

    def test_negated_discouraged_phrase_is_not_flagged(self):
        content = make_report().replace(
            "## 一、你5—10年后的人生画像\n",
            "## 一、你5—10年后的人生画像\n这不是唯一选择。\n",
        )

        quality = check_report_quality(content)

        self.assertNotIn("出现不建议表达：唯一选择", quality["warnings"])

    def test_template_phrase_is_flagged_for_rewrite(self):
        content = make_report().replace(
            "## 一、你5—10年后的人生画像\n",
            "## 一、你5—10年后的人生画像\n综合来看，",
        )

        quality = check_report_quality(content)

        self.assertEqual(quality["status"], "warning")
        self.assertIn("出现模板化表达：综合来看", quality["warnings"])

    def test_repeated_validation_term_is_flagged_for_friendlier_rewrite(self):
        quality = check_report_quality(make_report())

        self.assertTrue(
            any(item.startswith("学生可见文字反复使用生硬术语：验证") for item in quality["warnings"])
        )

    def test_a_few_validation_terms_do_not_create_a_style_warning(self):
        content = make_report().replace("验证", "尝试")
        content += "\n验证、验证、验证、验证"

        quality = check_report_quality(content)

        self.assertFalse(
            any(item.startswith("学生可见文字反复使用生硬术语：验证") for item in quality["warnings"])
        )

    def test_portrait_action_advice_is_flagged_for_rewrite(self):
        content = make_report().replace(
            "## 二、你的核心优势与风险短板",
            "你可以先完善简历，接下来半年投递实习。\n## 二、你的核心优势与风险短板",
        )

        quality = check_report_quality(content)

        self.assertTrue(
            any(item.startswith("人生画像混入当前分析或行动建议") for item in quality["warnings"])
        )

    def test_empty_plan_body_is_fatal(self):
        content = make_report().replace(
            "### Plan A：主攻路径\n" + "围绕当前最明确的目标建立主攻路径。下一步完成岗位访谈和一个真实项目，并以项目反馈作为继续投入或切换的条件。" * 7,
            "### Plan A：主攻路径\n",
        )

        quality = check_report_quality(content)

        self.assertEqual(quality["status"], "failed")
        self.assertIn("路径内容过少：Plan A", quality["fatalWarnings"])

    def test_bold_semantic_subheadings_are_recognized(self):
        content = make_report()
        for title in (
            "你现在最大的困惑是什么？",
            "这个困惑背后的真正问题是什么？",
            "接下来可以如何验证？",
            "Plan A：主攻路径",
            "Plan B：备选路径",
            "Plan C：系统建议路径",
        ):
            content = content.replace(f"### {title}", f"**{title}**")

        quality = check_report_quality(content)

        self.assertFalse(any("缺少关键内容" in item for item in quality["warnings"]))


if __name__ == "__main__":
    unittest.main()
