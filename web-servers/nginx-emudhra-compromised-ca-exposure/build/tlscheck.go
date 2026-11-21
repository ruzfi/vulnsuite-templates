// tlscheck connects to the local nginx, takes the certificate chain it
// presents, and checks it cryptographically: whether the leaf is signed by an
// intermediate whose public key is one of the eight compromised eMudhra keys
// (matched by SPKI SHA-256, not by name), or whether the chain verifies to the
// clean test root with no compromised key anywhere in it.
package main

import (
	"crypto/sha256"
	"crypto/tls"
	"crypto/x509"
	"encoding/hex"
	"encoding/pem"
	"fmt"
	"os"
)

const addr = "127.0.0.1:443"

var compromisedSPKI = map[string]string{
	"ebed6475c2c2d80fcb199f3fe8dd6e6b3ce60b77eb15d4e42c3dec0c6f5b5105": "EM DV TLS CA - G3B",
	"49dd353dc2b919a3770645117d0e60c16115e7d1bc259eefe734b00ea434fe5f": "EM DV TLS CA - G3C",
	"43bffa19d6ef651451f6841e019931e96f6f2eaeff28ab4b6f1ce4576de2717b": "EM OV TLS CA - G3B",
	"63ecefee431d49523bc1136c4e72d0206a477086caf606cd5cf025686c109cf8": "EM OV TLS CA - G3C",
	"e0254c7fcdc265e2f0f8a428dabb75ab4ae039b4872d62f5ee57f0877d5a8a41": "EM EV TLS CA - G3B",
	"5c0660a2b164910d8ff589c18e14552e9e0ec237dcefe2cb736d41a4811f81a0": "EM EV TLS CA - G3C",
	"ec4ffa1ad0ac88081314b7aaffef6a91f97cd57291bb5ba686c5415f5eb4f6b6": "EM OV CS CA - G3B",
	"92c063d67e8f14db71d288e11266ffdaf69cbf115f7bab14f3bc2f68d25e0e30": "EM OV CS CA - G3C",
}

func fail(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "FAIL: "+format+"\n", args...)
	os.Exit(1)
}

func spki(c *x509.Certificate) string {
	h := sha256.Sum256(c.RawSubjectPublicKeyInfo)
	return hex.EncodeToString(h[:])
}

func readCert(path string) *x509.Certificate {
	raw, err := os.ReadFile(path)
	if err != nil {
		fail("%v", err)
	}
	block, _ := pem.Decode(raw)
	if block == nil {
		fail("no PEM block in %s", path)
	}
	c, err := x509.ParseCertificate(block.Bytes)
	if err != nil {
		fail("%v", err)
	}
	return c
}

func main() {
	if len(os.Args) != 2 || (os.Args[1] != "--expect-compromised" && os.Args[1] != "--expect-clean") {
		fmt.Fprintln(os.Stderr, "usage: tlscheck --expect-compromised|--expect-clean")
		os.Exit(2)
	}
	conn, err := tls.Dial("tcp", addr, &tls.Config{InsecureSkipVerify: true, ServerName: "localhost"})
	if err != nil {
		fail("TLS handshake with %s: %v", addr, err)
	}
	chain := conn.ConnectionState().PeerCertificates
	conn.Close()
	if len(chain) < 2 {
		fail("%s presented %d certificate(s), want leaf + intermediate", addr, len(chain))
	}
	leaf := chain[0]

	compromisedIssuer := ""
	for _, c := range chain[1:] {
		if name, ok := compromisedSPKI[spki(c)]; ok && leaf.CheckSignatureFrom(c) == nil {
			compromisedIssuer = name
		}
	}

	switch os.Args[1] {
	case "--expect-compromised":
		if compromisedIssuer == "" {
			fail("leaf is not signed by any compromised eMudhra intermediate key")
		}
		root := readCert("/app/certs/emsign-root-tls-ca-g3.pem")
		if err := chain[1].CheckSignatureFrom(root); err != nil {
			fail("presented intermediate does not chain to emSign Root TLS CA - G3: %v", err)
		}
		fmt.Printf("PASS: %s presents a leaf signed by a compromised eMudhra intermediate key (spki sha256 %s), chaining to emSign Root TLS CA - G3\n", addr, spki(chain[1]))
	case "--expect-clean":
		for _, c := range chain {
			if name, ok := compromisedSPKI[spki(c)]; ok {
				fail("presented chain still contains the compromised key of %s", name)
			}
		}
		roots := x509.NewCertPool()
		roots.AddCert(readCert("/app/certs/clean-root.pem"))
		inters := x509.NewCertPool()
		for _, c := range chain[1:] {
			inters.AddCert(c)
		}
		if _, err := leaf.Verify(x509.VerifyOptions{Roots: roots, Intermediates: inters, DNSName: "localhost"}); err != nil {
			fail("presented chain does not verify to the clean root: %v", err)
		}
		fmt.Printf("PASS: %s presents a chain that verifies to the clean test root; no compromised eMudhra key in the presented chain\n", addr)
	}
}
