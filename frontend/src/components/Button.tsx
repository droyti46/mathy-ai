import { ButtonHTMLAttributes } from 'react';

export default function Button(props: ButtonHTMLAttributes<HTMLButtonElement>) {
  const { className = '', ...rest } = props;
  return (
    <button
      className={
        'rounded-xl2 px-6 py-3 font-semibold shadow-card bg-primary-900 text-white hover:bg-primary-500 transition ' +
        className
      }
      {...rest}
    />
  );
}
