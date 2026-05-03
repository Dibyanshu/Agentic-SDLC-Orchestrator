import type { TextareaHTMLAttributes } from "react";

export function Textarea({ className = "", ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={`resize-none rounded-md border border-slate-300 bg-white p-3 text-sm leading-6 outline-none focus:border-primary focus:ring-2 focus:ring-blue-100 ${className}`}
      {...props}
    />
  );
}
