import { InputHTMLAttributes } from 'react';

export default function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  const { className = '', ...rest } = props;
  return (
    <input
      className={
        'w-full rounded-full px-5 py-3 bg-white shadow-inner outline-none ring-0 focus:ring-2 focus:ring-primary-500 ' +
        className
      }
      {...rest}
    />
  );
}
