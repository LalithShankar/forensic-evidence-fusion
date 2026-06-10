import { render, screen } from "@testing-library/react";
import { ChakraProvider, defaultSystem } from "@chakra-ui/react";
import type { ReactElement } from "react";
import { describe, expect, it } from "vitest";

import { ClassificationBadge } from "./ClassificationBadge";
import { makeArtifact } from "../../test/fixtures";

function renderBadge(ui: ReactElement) {
  return render(<ChakraProvider value={defaultSystem}>{ui}</ChakraProvider>);
}

describe("ClassificationBadge", () => {
  it("shows suggestion and confidence for a classified artifact", () => {
    const artifact = makeArtifact({
      suggested_source_group: "ThirdParty",
      suggested_source_family: "WhatsApp",
      classification_confidence: 0.92,
      classification_reason: "Filename matches WhatsApp export pattern",
    });

    renderBadge(<ClassificationBadge artifact={artifact} />);

    expect(screen.getByText(/ThirdParty \/ WhatsApp/)).toBeInTheDocument();
    expect(screen.getByText(/Confidence: 92%/)).toBeInTheDocument();
    expect(
      screen.getByText(/Filename matches WhatsApp export pattern/),
    ).toBeInTheDocument();
  });

  it("renders nothing when there is no suggestion or confidence", () => {
    const artifact = makeArtifact();
    const { container } = renderBadge(
      <ClassificationBadge artifact={artifact} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("shows a dash when confidence is missing but a suggestion exists", () => {
    const artifact = makeArtifact({
      suggested_source_group: "Google",
      suggested_source_family: "Takeout",
      classification_confidence: null,
    });

    renderBadge(<ClassificationBadge artifact={artifact} />);

    expect(screen.getByText(/Google \/ Takeout/)).toBeInTheDocument();
    expect(screen.getByText(/Confidence: —/)).toBeInTheDocument();
  });
});
