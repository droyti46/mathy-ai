import { useParams, Link } from 'react-router-dom';

export default function TaskPage() {
  const { taskId } = useParams();
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4">
      <div className="text-2xl font-bold">Задача {taskId}</div>
      <div className="opacity-80">Здесь позже будет режим решения/преподавания</div>
      <Link to="/app/tasks" className="text-primary-900 underline">← Вернуться к заданиям</Link>
    </div>
  );
}
