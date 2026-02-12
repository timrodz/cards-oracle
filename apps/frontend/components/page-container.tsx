import { PropsWithChildren } from "react";

export function PageContainer({ children }: PropsWithChildren) {
  return (
    <div className="pt-6 pb-12 px-4 md:px-8 flex flex-col items-center gap-6">
      {children}
    </div>
  );
}
