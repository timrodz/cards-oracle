"use client";

import { ElevenlabsConversation } from "./components/elevenlabs-conversation";
import { ScryfallCardFilters } from "./components/scryfall-card-filters";
import { ScryfallCards } from "./components/scryfall-card-list";
import { useScryfallCards } from "./viewModels/use-scryfall-cards";

export function ScryfallCardSearchFeature() {
  const {
    data: {
      allCards,
      filteredCards,
      hasMoreCards,
      cmcOptions,
      colorOptions,
      setNameOptions,
      selectedCmc,
      selectedColors,
      selectedSetName,
      isLoadingMore,
    },
    operations: {
      loadMoreCards,
      onHandleScryfallCardSearch,
      onHandleScryfallCardFilterer,
      setSelectedCmc,
      setSelectedColors,
      setSelectedSetName,
    },
  } = useScryfallCards({
    initialData: undefined,
  });

  return (
    <main className="z-10 flex-1 w-full max-w-6xl mx-auto flex flex-col items-center justify-start min-h-0 relative gap-4">
      <div className="flex flex-col items-center gap-2">
        <h1 className="text-3xl">Welcome to the Card oracle</h1>
        <p className="text-lg text-muted-foreground">
          {`A real-time voice translating tool to help you find Magic: The Gathering cards`}
        </p>
      </div>

      <ElevenlabsConversation
        onScryfallCardSearch={onHandleScryfallCardSearch}
        onScryfallCardFilterer={onHandleScryfallCardFilterer}
      />

      {allCards.length > 0 && (
        <ScryfallCardFilters
          cmcOptions={cmcOptions}
          selectedCmc={selectedCmc}
          onCmcChange={setSelectedCmc}
          colorOptions={colorOptions}
          selectedColors={selectedColors}
          onColorsChange={setSelectedColors}
          setNameOptions={setNameOptions}
          selectedSetName={selectedSetName}
          onSetNameChange={setSelectedSetName}
        />
      )}

      <ScryfallCards
        filteredCards={filteredCards}
        hasMoreCards={hasMoreCards}
        isLoadingMore={isLoadingMore}
        loadMoreCards={loadMoreCards}
      />
    </main>
  );
}
