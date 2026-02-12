import {
  ComboboxContent,
  ComboboxChipsInput,
  Combobox,
  ComboboxInput,
  ComboboxEmpty,
  ComboboxList,
  ComboboxItem,
  ComboboxChips,
  ComboboxChip,
} from "@/components/ui/combobox";
import { scryfallColorToLabel } from "@/lib/scryfall";
import { ScryfallCardColor } from "@/lib/types/scryfall";

interface FiltersProps {
  selectedCmc: number | null;
  selectedColors: ScryfallCardColor[] | null;
  selectedSetName: string | null;
  cmcOptions: number[];
  colorOptions: ScryfallCardColor[];
  setNameOptions: string[];
  onCmcChange: (cmc: number | null) => void;
  onColorsChange: (colors: ScryfallCardColor[]) => void;
  onSetNameChange: (setName: string | null) => void;
}

export function ScryfallCardFilters({
  selectedCmc,
  selectedSetName,
  selectedColors,
  cmcOptions,
  colorOptions,
  setNameOptions,
  onCmcChange,
  onColorsChange,
  onSetNameChange,
}: FiltersProps) {
  return (
    <div className="flex w-full flex-wrap items-center justify-center gap-4">
      <Combobox
        items={cmcOptions}
        value={selectedCmc}
        onValueChange={(value) => onCmcChange(value)}
      >
        <ComboboxInput
          placeholder="Filter by CMC"
          showClear
          aria-label="Filter by CMC"
        />
        <ComboboxContent>
          <ComboboxEmpty>No CMC values found.</ComboboxEmpty>
          <ComboboxList>
            {(item) => (
              <ComboboxItem key={item} value={item}>
                {item}
              </ComboboxItem>
            )}
          </ComboboxList>
        </ComboboxContent>
      </Combobox>
      <div className="flex w-[320px] flex-none items-center gap-2">
        <Combobox
          multiple
          items={colorOptions}
          value={selectedColors}
          onValueChange={(value) => onColorsChange(value ?? [])}
        >
          <ComboboxChips className="w-[320px] min-w-[320px]">
            {selectedColors?.map((color) => (
              <ComboboxChip key={color}>
                {scryfallColorToLabel(color)}
              </ComboboxChip>
            ))}
            <ComboboxChipsInput
              placeholder="Filter by Color"
              aria-label="Filter by color"
            />
          </ComboboxChips>
          <ComboboxContent>
            <ComboboxEmpty>No color values found.</ComboboxEmpty>
            <ComboboxList>
              {(color) => (
                <ComboboxItem key={color} value={color}>
                  {scryfallColorToLabel(color)}
                </ComboboxItem>
              )}
            </ComboboxList>
          </ComboboxContent>
        </Combobox>
      </div>
      <Combobox
        items={setNameOptions}
        value={selectedSetName}
        onValueChange={(value) => onSetNameChange(value)}
      >
        <ComboboxInput
          placeholder="Filter by Set"
          showClear
          aria-label="Filter by set name"
        />
        <ComboboxContent>
          <ComboboxEmpty>No set values found.</ComboboxEmpty>
          <ComboboxList>
            {(setName) => (
              <ComboboxItem key={setName} value={setName}>
                {setName}
              </ComboboxItem>
            )}
          </ComboboxList>
        </ComboboxContent>
      </Combobox>
    </div>
  );
}
