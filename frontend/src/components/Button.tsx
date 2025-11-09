import { ButtonHTMLAttributes } from 'react';

export default function Button(props: ButtonHTMLAttributes<HTMLButtonElement>) {
  const { className = '', ...rest } = props;
  return (
    <button
      className={
        'rounded-xl2 px-6 py-3 font-semibold text-white hover:scale-105 transition ' +
        className
      }
      {...rest}
    />
  );
}
