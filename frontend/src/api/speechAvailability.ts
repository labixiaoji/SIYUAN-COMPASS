import { fetchSpeechStatus } from "./speech";

// 学校生产环境默认关闭语音。未配置时不展示一个点击后必然返回 503 的按钮。
// 多个问卷字段会复用该状态，因此只请求一次。
let cached: Promise<boolean> | null = null;

export function isSpeechConfigured(): Promise<boolean> {
  if (!cached) {
    cached = fetchSpeechStatus()
      .then((status) => status.configured)
      .catch(() => false);
  }
  return cached;
}

export function resetSpeechAvailabilityCache() {
  cached = null;
}
