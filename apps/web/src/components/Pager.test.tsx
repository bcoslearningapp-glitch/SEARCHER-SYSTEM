import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { getDictionary } from "@/lib/i18n";

import { PAGE_SIZE, Pager, pageNumber, pageQuery, pageSlice } from "./Pager";

describe("Pager", () => {
  const dict = getDictionary("en");
  const href = (n: number) => `/en/library?page=${n}`;

  it("reads invalid page params as page 1", () => {
    expect(["", "0", "-2", "1.5", "abc", undefined].map(pageNumber)).toEqual([1, 1, 1, 1, 1, 1]);
    expect(pageNumber("3")).toBe(3);
  });

  it("asks for one extra item to detect a next page", () => {
    expect(pageQuery(3)).toBe(`limit=${PAGE_SIZE + 1}&offset=${2 * PAGE_SIZE}`);
    const full = Array.from({ length: PAGE_SIZE + 1 }, (_, i) => i);
    expect(pageSlice(full)).toEqual({ items: full.slice(0, PAGE_SIZE), hasNext: true });
    expect(pageSlice([1, 2])).toEqual({ items: [1, 2], hasNext: false });
  });

  it("renders nothing when everything fits on one page", () => {
    const { container } = render(<Pager page={1} hasNext={false} href={href} dict={dict} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("links to the neighbouring pages", () => {
    render(<Pager page={2} hasNext href={href} dict={dict} />);
    expect(screen.getByRole("link", { name: /Previous/ })).toHaveAttribute("href", "/en/library?page=1");
    expect(screen.getByRole("link", { name: /Next/ })).toHaveAttribute("href", "/en/library?page=3");
  });
});
