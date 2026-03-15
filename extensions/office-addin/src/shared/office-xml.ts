/**
 * Office Custom XML Parts interop for AKF metadata.
 *
 * Matches the Python SDK's _ooxml.py format:
 *   Namespace: https://akf.dev/v1
 *   XML wrapper: <akf:metadata xmlns:akf="..."><![CDATA[...json...]]></akf:metadata>
 */

import { AKFMetadata } from "./akf-core";

const AKF_NAMESPACE = "https://akf.dev/v1";

function wrapXml(json: string): string {
  return (
    '<?xml version="1.0" encoding="UTF-8"?>\n' +
    `<akf:metadata xmlns:akf="${AKF_NAMESPACE}">\n` +
    `<![CDATA[\n${json}\n]]>\n` +
    "</akf:metadata>"
  );
}

function parseCdata(xml: string): string | null {
  const match = xml.match(/<!\[CDATA\[\s*([\s\S]*?)\s*\]\]>/);
  return match ? match[1] : null;
}

export async function extractAKF(): Promise<AKFMetadata | null> {
  return new Promise((resolve) => {
    Office.context.document.customXmlParts.getByNamespaceAsync(
      AKF_NAMESPACE,
      (result) => {
        if (
          result.status !== Office.AsyncResultStatus.Succeeded ||
          result.value.length === 0
        ) {
          resolve(null);
          return;
        }

        const part = result.value[0];
        part.getXmlAsync((xmlResult) => {
          if (xmlResult.status !== Office.AsyncResultStatus.Succeeded) {
            resolve(null);
            return;
          }

          const jsonStr = parseCdata(xmlResult.value);
          if (!jsonStr) {
            resolve(null);
            return;
          }

          try {
            const raw = JSON.parse(jsonStr);
            resolve(normalizeCompact(raw) as unknown as AKFMetadata);
          } catch {
            resolve(null);
          }
        });
      }
    );
  });
}

export async function embedAKF(metadata: AKFMetadata): Promise<void> {
  // Remove existing AKF parts first
  await removeExistingAKF();

  const json = JSON.stringify(metadata, null, 2);
  const xml = wrapXml(json);

  return new Promise((resolve, reject) => {
    Office.context.document.customXmlParts.addAsync(xml, (result) => {
      if (result.status === Office.AsyncResultStatus.Succeeded) {
        resolve();
      } else {
        reject(new Error("Failed to embed AKF metadata"));
      }
    });
  });
}

/**
 * Normalize compact wire format keys to descriptive field names.
 * Mirrors the Python SDK's normalize logic: c→content, t→confidence, etc.
 */
function normalizeCompact(raw: Record<string, unknown>): Record<string, unknown> {
  const CLAIM_MAP: Record<string, string> = {
    c: "content", t: "confidence", src: "source",
    tier: "authority_tier", ai: "ai_generated", v: "verified",
  };
  const TOP_MAP: Record<string, string> = {
    ver: "version", cls: "classification", prov: "provenance",
    hash: "integrity_hash",
  };

  // Normalize top-level keys
  for (const [compact, full] of Object.entries(TOP_MAP)) {
    if (raw[compact] !== undefined && raw[full] === undefined) {
      raw[full] = raw[compact];
      delete raw[compact];
    }
  }

  // Normalize claims
  const claims = raw.claims as Record<string, unknown>[] | undefined;
  if (Array.isArray(claims)) {
    for (const claim of claims) {
      for (const [compact, full] of Object.entries(CLAIM_MAP)) {
        if (claim[compact] !== undefined && claim[full] === undefined) {
          claim[full] = claim[compact];
          delete claim[compact];
        }
      }
    }
  }

  return raw;
}

async function removeExistingAKF(): Promise<void> {
  return new Promise((resolve) => {
    Office.context.document.customXmlParts.getByNamespaceAsync(
      AKF_NAMESPACE,
      (result) => {
        if (
          result.status !== Office.AsyncResultStatus.Succeeded ||
          result.value.length === 0
        ) {
          resolve();
          return;
        }

        let remaining = result.value.length;
        for (const part of result.value) {
          part.deleteAsync(() => {
            remaining--;
            if (remaining === 0) resolve();
          });
        }
      }
    );
  });
}
