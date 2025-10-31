import { useSearchParams } from 'react-router-dom';
import SolveLayout from './SolveMode/SolveLayout';
import TeachLayout from './TeachMode/TeachLayout';

export default function TaskPage() {
  const [sp] = useSearchParams();
  const mode = sp.get('mode') ?? 'solve';
  return mode === 'teach' ? <TeachLayout /> : <SolveLayout />;
}
