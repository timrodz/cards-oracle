import { ScryfallCardFace, type ScryfallCard } from "@/lib/types/scryfall";
import Image from "next/image";
import { AnimatePresence, motion, useInView } from "motion/react";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { RefreshCcwIcon } from "lucide-react";

function getCardImageUrl(
  card: ScryfallCard | ScryfallCardFace,
): string | undefined {
  return card.image_uris?.normal;
}

function isCardDoubleFaced(card: ScryfallCard): boolean {
  // Cards can have multiple faces but no image_uris on them, probably meaning it's an adventure type card
  return card.card_faces
    ? card.card_faces.length > 0 &&
        card.card_faces.some((face) => !!face.image_uris)
    : false;
}

interface ScryfallCardFaceImageProps {
  url: string;
  label: string;
}

function ScryfallCardFaceImage({ url, label }: ScryfallCardFaceImageProps) {
  return (
    <Image
      className="rounded-[20px] sm:rounded-[16px] md:rounded-[12px] lg:rounded-[8px]"
      src={url}
      alt={label}
      width={488}
      height={680}
      quality={75}
      decoding="async"
      loading="lazy"
    />
  );
}

interface ScryfallCardOverviewProps {
  card: ScryfallCard;
}

function SingleFaceCardImage({
  card,
  shouldRenderImage,
}: {
  card: ScryfallCard;
  shouldRenderImage: boolean;
}) {
  const imageUrl = getCardImageUrl(card);
  if (!imageUrl) {
    return null;
  }

  return shouldRenderImage ? (
    <ScryfallCardFaceImage url={imageUrl} label={card.name} />
  ) : (
    <div
      className="scryfall-card-image bg-muted/20"
      style={{ width: 488, height: 680 }}
    />
  );
}

function DoubleFacedCardImages({
  card,
  shouldRenderImage,
}: {
  card: ScryfallCard;
  shouldRenderImage: boolean;
}) {
  const [activeFaceIndex, setActiveFaceIndex] = useState(0);

  if (!card.card_faces?.length) {
    return <p>No image</p>;
  }

  const activeFace = card.card_faces[activeFaceIndex];
  const activeFaceImageUrl = getCardImageUrl(activeFace);
  const faceCount = card.card_faces.length;
  const nextFaceIndex = (activeFaceIndex + 1) % faceCount;

  if (!shouldRenderImage) return null;

  return (
    <div className="relative flex flex-col items-center gap-3">
      {activeFaceImageUrl ? (
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={activeFaceIndex}
            style={{ transformStyle: "preserve-3d" }}
            initial={{ rotateY: -90, opacity: 0 }}
            animate={{ rotateY: 0, opacity: 1 }}
            exit={{ rotateY: 90, opacity: 0 }}
            transition={{ duration: 0.1, ease: "easeInOut" }}
          >
            <div>
              <ScryfallCardFaceImage
                url={activeFaceImageUrl}
                label={activeFace.name}
              />
            </div>
          </motion.div>
        </AnimatePresence>
      ) : null}
      <Button
        className="absolute -right-[5%] top-[35%] -translate-y-1/2 rounded"
        type="button"
        onClick={() => setActiveFaceIndex(nextFaceIndex)}
      >
        <motion.span
          className="flex"
          animate={{ rotateZ: -360 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          key={activeFaceIndex}
        >
          <RefreshCcwIcon />
        </motion.span>
      </Button>
    </div>
  );
}

export function ScryfallCardOverview({ card }: ScryfallCardOverviewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const isInView = useInView(containerRef, { amount: 0.15, once: true });

  return (
    <motion.div
      ref={containerRef}
      initial="out"
      animate={isInView ? "in" : "out"}
      variants={{
        in: { opacity: 1, scale: 1 },
        out: { opacity: 0, scale: 0.96 },
      }}
      transition={{ duration: 0.2, ease: "easeOut" }}
    >
      {isCardDoubleFaced(card) ? (
        <DoubleFacedCardImages card={card} shouldRenderImage={isInView} />
      ) : (
        <SingleFaceCardImage card={card} shouldRenderImage={isInView} />
      )}
    </motion.div>
  );
}
