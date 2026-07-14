import { useEffect, useState } from "react";
import { getThumb } from "../wikiThumb";

interface Props {
  wiki?: string | null;
  name: string;
  size?: number;
}

export default function PoiThumb({ wiki, name, size = 40 }: Props) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    if (wiki) {
      getThumb(wiki).then((u) => {
        if (alive) setUrl(u);
      });
    } else {
      setUrl(null);
    }
    return () => {
      alive = false;
    };
  }, [wiki]);

  if (!url) return null;
  return (
    <img
      src={url}
      alt={name}
      loading="lazy"
      className="rounded-md object-cover"
      style={{ width: size, height: size }}
    />
  );
}
