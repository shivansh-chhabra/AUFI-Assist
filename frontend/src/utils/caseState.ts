import type { ChatMessage } from '../types';

/** Where the case is, worked out from the message list. */
export function deriveCase(messages: ChatMessage[]) {
  const last = messages[messages.length - 1];
  const progress = [...messages].reverse().find((m) => m.progress)?.progress;
  const finished = !!progress?.stopReason;
  return {
    last,
    progress,
    finished,
    /** A case is under way and its question screen should be showing. */
    inCase: messages.length > 0 && !finished,
    awaitingAnswer: !!(last?.role === 'ai' && last.question),
  };
}
