import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

export default function Markdown({
  children,
  className,
}: { children: string; className?: string }) {
  return (
    <ReactMarkdown
      className={className}
      remarkPlugins={[remarkMath]}
      rehypePlugins={[rehypeKatex]}
      // при желании можно ограничить набор HTML-тегов через components / allowedElements
    >
      {children}
    </ReactMarkdown>
  );
}
