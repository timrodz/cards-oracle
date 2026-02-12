import { PageContainer } from "@/components/page-container";
import { ScryfallCardSearchFeature } from "@/features/scryfall-card-search/card-oracle-agent-feature";

export default function Home() {
  return (
    <PageContainer>
      <ScryfallCardSearchFeature />
    </PageContainer>
  );
}
