import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function randomInRange(min: number, max: number, decimals = 2): number {
  const value = Math.random() * (max - min) + min
  return parseFloat(value.toFixed(decimals))
}

export function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

const AMINO_ACIDS = 'ACDEFGHIKLMNPQRSTVWY'

export function generateSequence(length: number): string {
  return Array.from({ length }, () =>
    AMINO_ACIDS[Math.floor(Math.random() * AMINO_ACIDS.length)]
  ).join('')
}
