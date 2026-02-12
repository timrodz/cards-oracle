import { ScryfallCardOverview } from "@/features/scryfall-card-search/components/scryfall-card";
import { Button } from "@/components/ui/button";
import { ScryfallCard } from "@/lib/types/scryfall";

interface ScryfallCardsProps {
  filteredCards: ScryfallCard[];
  hasMoreCards: boolean;
  isLoadingMore: boolean;
  loadMoreCards: () => void;
}

export function ScryfallCards({
  filteredCards,
  hasMoreCards,
  isLoadingMore,
  loadMoreCards,
}: ScryfallCardsProps) {
  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {filteredCards.map((card) => (
          <ScryfallCardOverview key={card.id} card={card} />
        ))}
      </div>
      {hasMoreCards && (
        <Button onClick={loadMoreCards} disabled={isLoadingMore}>
          {isLoadingMore ? "Loading..." : "Load More"}
        </Button>
      )}
    </>
  );
}
