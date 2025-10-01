import React from 'react'
import Navigation from '../../src/components/Navigation'
import { mount } from 'cypress/react'
import { MemoryRouter } from 'react-router-dom'

describe('<Navigation />', () => {
  it('renders', () => {
    mount(
    <MemoryRouter>
      <Navigation />
    </MemoryRouter>
  )
  })
})