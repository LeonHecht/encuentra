import { useCallback, useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import type { ChatStatus } from "ai";
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools,
} from "@/components/ai-elements/prompt-input";
import { cn } from "@/lib/utils";

type ExpandingPromptInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void | Promise<void>;
  placeholder?: string;
  status?: ChatStatus;
  disabled?: boolean;
  onStop?: () => void;
  className?: string;
  textareaClassName?: string;
};

export default function ExpandingPromptInput({
  value,
  onChange,
  onSubmit,
  placeholder = "Pregunta lo que quieras",
  status = "ready",
  disabled = false,
  onStop,
  className,
  textareaClassName,
}: ExpandingPromptInputProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const updateExpanded = useCallback((textarea: HTMLTextAreaElement) => {
    requestAnimationFrame(() => {
      const styles = window.getComputedStyle(textarea);
      const lineHeight = Number.parseFloat(styles.lineHeight) || 24;
      const paddingY =
        (Number.parseFloat(styles.paddingTop) || 0) +
        (Number.parseFloat(styles.paddingBottom) || 0);
      const singleLineHeight = lineHeight + paddingY;

      setIsExpanded(
        textarea.value.length > 0 && textarea.scrollHeight > singleLineHeight + 2
      );
    });
  }, []);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea || value) return;
    setIsExpanded(false);
  }, [value]);

  function handleChange(event: ChangeEvent<HTMLTextAreaElement>) {
    onChange(event.currentTarget.value);
    updateExpanded(event.currentTarget);
  }

  function handleSubmit(_message: unknown, event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <PromptInput
      onSubmit={handleSubmit}
      className={cn(
        "bg-white shadow-lg transition-[background-color,border-radius] hover:bg-gray-50",
        isExpanded ? "rounded-[28px]" : "rounded-full",
        disabled && "opacity-75",
        className
      )}
    >
      <PromptInputBody>
        <PromptInputTextarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          placeholder={placeholder}
          disabled={disabled}
          className={cn("py-3 pl-4 pr-14 leading-6", textareaClassName)}
        />
      </PromptInputBody>
      <PromptInputFooter
        className={cn(
          "absolute right-2 w-auto px-0 py-0",
          isExpanded ? "bottom-2" : "top-1/2 -translate-y-1/2"
        )}
      >
        <PromptInputTools />
        <PromptInputSubmit
          className="rounded-full"
          disabled={disabled || (status !== "streaming" && !value.trim())}
          status={status}
          onClick={(event) => {
            if (status === "streaming") {
              event.preventDefault();
              onStop?.();
            }
          }}
        />
      </PromptInputFooter>
    </PromptInput>
  );
}
