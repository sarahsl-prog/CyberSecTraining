import React from 'react';
import styles from './SkipLink.module.css';

interface SkipLinkProps {
  href: string;
  children: React.ReactNode;
}

/**
 * Skip link component for keyboard navigation.
 * Allows users to skip to main content, bypassing navigation.
 * Only visible when focused (for screen reader and keyboard users).
 */
export function SkipLink({ href, children }: SkipLinkProps) {
  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const target = document.querySelector(href);
    if (target) {
      // Focus the target element
      (target as HTMLElement).focus();
      // Scroll into view
      target.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <a href={href} className={styles.skipLink} onClick={handleClick}>
      {children}
    </a>
  );
}

export default SkipLink;
