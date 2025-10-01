import React from 'react'
import AnimatedBackground from '../../src/components/AnimationBackground'
import { mount } from 'cypress/react'
import { MemoryRouter } from 'react-router-dom'

describe('<AnimatedBackground />', () => {
  it('renders', () => {
    mount(
    <MemoryRouter>
      <AnimatedBackground/>
    </MemoryRouter>
    )
  })
})