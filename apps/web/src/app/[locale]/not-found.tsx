import Link from "next/link";

import { getDictionary } from "@/lib/i18n";

/** A missing page or record (404). Localised text needs the locale, which not-found pages do not receive. */
export default function NotFound() {
  const dict = getDictionary("en");
  return (
    <div className="space-y-3 p-6" data-testid="page-not-found">
      <p>{dict.ui.pageNotFound}</p>
      <Link href="/" className="underline">
        {dict.ui.backToDesk}
      </Link>
    </div>
  );
}
