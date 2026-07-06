"use client";

import { useRef, useState, type KeyboardEvent } from "react";

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
              className="flex items-center gap-1.5 rounded-lg bg-gray-100 px-2.5 py-1 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-200"
            >
              <span className="max-w-40 truncate">{file.name}</span>
              <button
                type="button"
                aria-label={`Remove ${file.name}`}
                onClick={() => removeFile(i)}
                className="text-gray-400 hover:text-red-500"
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}

      {files.length > 0 && value.trim().length === 0 && (
        <p className="text-xs text-amber-600 dark:text-amber-400">
          Add a text prompt — the file can’t be sent on its own.
        </p>
      )}

      <div className="flex items-end gap-2">
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
          className="h-11 shrink-0 rounded-xl border border-gray-300 px-3 text-sm text-gray-600 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
        >
          📎
        </button>
        <textarea
          aria-label="Message"
          rows={1}
          value={value}
          disabled={disabled}
          placeholder={placeholder}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          className="max-h-40 min-h-11 flex-1 resize-none rounded-xl border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 outline-none focus:border-blue-500 disabled:opacity-60 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
        />
        <button
          type="button"
          onClick={submit}
          disabled={!canSubmit}
          className="h-11 shrink-0 rounded-xl bg-blue-600 px-4 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
