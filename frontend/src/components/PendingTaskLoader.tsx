import spinner from '@/assets/chat/spinner.svg';

interface PendingProps {
  pendingMessage?: string;
}

export const PendingTaskLoader = ({ pendingMessage }: PendingProps) => {
  return (
    <div className="flex flex-col gap-[12px]">
      <div className="flex items-center gap-[8px]">
        <img
          src={spinner}
          alt="pending"
          className="h-[24px] w-[24px] animate-spin"
        />
        <span className="text-gray6 text-[16px] font-[500]">
          {pendingMessage}
        </span>
      </div>

      <div className="flex w-fit items-center rounded-[32px] bg-gray2 py-[4px] pl-[4px] pr-[6px]">
        <div className="flex items-center">
          <div className="z-30 h-[18px] w-[18px] rounded-full bg-gray-300" />
          <div className="z-20 -ml-[6px] h-[18px] w-[18px] rounded-full bg-gray-900" />
          <div className="z-10 -ml-[6px] h-[18px] w-[18px] rounded-full bg-gray-300" />
        </div>
        <span className="ml-[4px] text-[12px] font-[500] text-gray5">+ 10</span>
      </div>
    </div>
  );
};
