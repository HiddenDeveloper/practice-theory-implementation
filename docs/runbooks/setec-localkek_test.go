package main

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

func TestLocalKEKRoundTrip(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "kek.json")

	// First call creates the keyset file.
	k1, err := localKEK(path)
	if err != nil {
		t.Fatalf("localKEK (create): %v", err)
	}
	info, err := os.Stat(path)
	if err != nil {
		t.Fatalf("keyset file not written: %v", err)
	}
	if perm := info.Mode().Perm(); perm != 0600 {
		t.Errorf("keyset perms = %o, want 600", perm)
	}

	plaintext := []byte("LINE_CHANNEL_ACCESS_TOKEN value")
	ad := []byte("setec")
	ct, err := k1.Encrypt(plaintext, ad)
	if err != nil {
		t.Fatalf("encrypt: %v", err)
	}
	if bytes.Contains(ct, plaintext) {
		t.Fatal("ciphertext contains plaintext — not encrypted")
	}

	// Second call must load the SAME keyset and decrypt what the first wrote.
	k2, err := localKEK(path)
	if err != nil {
		t.Fatalf("localKEK (reload): %v", err)
	}
	got, err := k2.Decrypt(ct, ad)
	if err != nil {
		t.Fatalf("decrypt with reloaded keyset: %v", err)
	}
	if !bytes.Equal(got, plaintext) {
		t.Fatalf("round-trip mismatch: got %q want %q", got, plaintext)
	}

	// A different keyset must NOT decrypt it.
	other, err := localKEK(filepath.Join(dir, "other.json"))
	if err != nil {
		t.Fatalf("localKEK (other): %v", err)
	}
	if _, err := other.Decrypt(ct, ad); err == nil {
		t.Fatal("decrypt succeeded with a foreign keyset — keys not isolated")
	}
}
