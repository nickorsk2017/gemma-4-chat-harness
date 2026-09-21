"use client";

import { useRef, useState, type KeyboardEvent } from "react";
import { PaperclipIcon, SendIcon } from "@/shared/ui-kit/icons";

const ACCEPTED_TYPES =
  "application/pdf,image/png,image/jpeg,image/webp,image/gif";

interface MessageInputProps {
  onSend: (text: string, files: File[]) => void;
  disabled?: boolean;
  placeholder?: string;
}

/**
 * Presentational composer. Owns only its local draft text + attached file.
 * No store/service access — emits them via `onSend`.
 *
 * At most ONE attachment (image / PDF) per message — picking another file
 * replaces the current one. The TEXT PROMPT IS MANDATORY — a file can never
 * be submitted without it.
 */
export function MessageInput({
  onSend,
  disabled = false,
  placeholder = "Message the agent…",
}: MessageInputProps) {
  const [value, setValue] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const canSubmit = value.trim().length > 0 && !disabled;

  const submit = () => {
    const text = value.trim();
    if (!text || disabled) return; // prompt is mandatory, even with files attached
    onSend(text, files);
    setValue("");
    setFiles([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const addFiles = (list: FileList | null) => {
    if (!list || list.length === 0) return;
    // Single-attachment policy: the new pick replaces the current file.
    setFiles([list[0]]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const removeFile = (index: number) =>
    setFiles((prev) => prev.filter((_, i) => i !== index));

  return (
    <div className="flex flex-col gap-2">
      {files.length > 0 && (
        <ul className="flex flex-wrap gap-2" aria-label="Attached files">
          {files.map((file, i) => (
            <li
              key={`${file.name}-${i}`}
              className="flex items-center gap-1.5 rounded-control bg-page px-2.5 py-1 text-xs text-foreground"
            >
              <span className="max-w-40 truncate">{file.name}</span>
              <button
                type="button"
                aria-label={`Remove ${file.name}`}
                onClick={() => removeFile(i)}
                className="text-muted transition-colors hover:text-danger"
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}

      {files.length > 0 && value.trim().length === 0 && (
        <p className="px-1 text-xs text-warning">
          Add a text prompt — the file can’t be sent on its own.
        </p>
      )}

      <div className="flex items-end gap-3 rounded-card border border-hairline bg-surface p-2">
        <input
          ref={fileInputRef}
          type="file"
          hidden
          accept={ACCEPTED_TYPES}
          aria-label="Attach a file"
          onChange={(e) => addFiles(e.target.files)}
        />
        <button
          type="button"
          aria-label="Attach image or PDF (one file)"
          title="Attach image or PDF (one file — a new pick replaces it)"
          disabled={disabled}
          onClick={() => fileInputRef.current?.click()}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-hairline text-muted transition-colors hover:bg-page hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
        >
          <PaperclipIcon className="h-5 w-5" />
        </button>
        <textarea
          aria-label="Message"
          rows={1}
          value={value}
          disabled={disabled}
          placeholder={placeholder}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          className="max-h-40 min-h-11 flex-1 resize-none self-center rounded-full border border-hairline bg-surface px-4 py-3 text-sm text-foreground placeholder:text-muted outline-none transition-colors focus:border-accent disabled:opacity-60"
        />
        <button
          type="button"
          onClick={submit}
          aria-label="Send message"
          disabled={!canSubmit}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-control bg-accent text-accent-foreground transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <SendIcon className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}
