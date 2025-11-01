import SplitPane from '@/components/SplitPane';
import TaskStatement from '@/pages/Main/TasksTab/TaskStatement';
import AttemptEditor from './AttemptEditor';
import AssistantChat from './AssistantChat';

export default function SolveLayout() {
  return (
    <div className="h-full">
      <SplitPane initial={[35, 35, 30]}>
        <TaskStatement />
        <AttemptEditor />
        <AssistantChat />
      </SplitPane>
    </div>
  );
}
