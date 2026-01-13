import numpy as np

class SimpleRNN:
    def __init__(
            self,
            input_size,
            hidden_size,
            output_size,
            W_ih=None,
            W_hh=None,
            W_ho=None,
            B_h=None,
            B_o=None
            ):
        # Weights for input to hidden, hidden to hidden, and hidden to output
        self.W_ih = W_ih if W_ih is not None else np.random.randn(hidden_size, input_size) * 0.01
        self.W_hh = W_hh if W_hh is not None else np.random.randn(hidden_size, hidden_size) * 0.01
        self.W_ho = W_ho if W_ho is not None else np.random.randn(output_size, hidden_size) * 0.01

        # Biases for hidden and output layers
        self.B_h = B_h if B_h is not None else np.random.randn(hidden_size) * 0.01
        self.B_o = B_o if B_o is not None else np.random.randn(output_size) * 0.01

    @classmethod
    def from_archive(cls, filepath):
        with np.load(filepath) as archive:
            kwargs = archive

            return cls(
                input_size=kwargs["W_ih"].shape[1],
                hidden_size=kwargs["B_h"].shape[0],
                output_size=kwargs["B_o"].shape[0],
                **kwargs
            )

    def save_to_archive(self, filepath):
        np.savez(filepath, W_ih=self.W_ih, W_hh=self.W_hh, W_ho=self.W_ho, B_h=self.B_h, B_o=self.B_o)

    def forward(self, inputs, initial_hidden_state=None, inspect=False):
        if inspect:
            return self.forward_inspect(inputs, initial_hidden_state)

        h = []
        y = []
 
        if initial_hidden_state is None:
            initial_hidden_state = np.zeros(self.B_h.shape)

        h_current = initial_hidden_state

        for x_t in inputs:
            # Calculate the hidden state:
            # - matmul input-hidden weights with the input (weight each input)
            # - matmul hidden-hidden weights with the current hidden state (weight each part of the memory)
            # - add those two together
            # now we have our total input signal: weighted inputs and weighted memory
            # - add the bias weights for the hidden layer (shift the activation function out of the origin) 
            # - tanh that
            h_current = np.tanh(self.W_ih @ x_t + self.W_hh @ h_current + self.B_h)
            # Calculate the output:
            # - matmul the hidden-output weights with the new hidden state (weight our new memory)
            # - add the output layer bias
            y_t = self.W_ho @ h_current + self.B_o

            h.append(h_current)
            y.append(y_t)

        return np.array(y), np.array(h)


    def forward_inspect(self, inputs, initial_hidden_state=None):
        h = []
        y = []


        if initial_hidden_state is None:
            initial_hidden_state = np.zeros(self.B_h.shape)

        h_current = initial_hidden_state

        for i in range(len(inputs)):
            print(f"\n****** input: {inputs[i]} *****")
            weighted_inputs = self.W_ih @ inputs[i]
            print(f"	weighted inputs:\n\t{weighted_inputs}")
            weighted_hidden = self.W_hh @ h_current
            print(f"	weighted hidden:\n\t{weighted_hidden}")
            signal = weighted_inputs + weighted_hidden + self.B_h
            print(f"	signal (wi + wh + bh):\n\t{signal}")
            h_current = np.tanh(signal)
            print(f"	new hidden:\n\t{h_current}")
            weighted_output = self.W_ho @ h_current
            print(f"	weighted out: \n\t{weighted_output}")
            output = weighted_output + self.B_o
            print(f"	out bias:\n\t{self.B_o}\n\nout: \t{output}")

            h.append(h_current)
            y.append(output)

        return np.array(y), np.array(h)



    def backward(self, predictions, targets, hidden_states, inputs, initial_hidden_state=None):
        if initial_hidden_state is None:
            initial_hidden_state = np.zeros(self.B_h.shape)

        # Derivatives of loss with respect to output, for each time t
        dl_dy = []
        # Derivates of loss with respect to hidden state, for each time t
        dl_dh = []        

        # 1: Loss with respect to output calculations for each time t
        for t in range(len(predictions)):
            dl_dy_t = 2 * (predictions[t] - targets[t]) / predictions.size # doing size for sequence_length * output size, as that is the product of the shape's dimensions (right?)
            # Store the output gradients for each time step
            dl_dy.append(dl_dy_t)

        # 2: Loss with respect to hidden state calculations for each time t
        # We work backwards through time for this one
        for t in range(len(predictions)-1, -1, -1):
            if t == len(predictions) -1:
                dl_dh_t = (self.W_ho.T @ dl_dy[-1]) * (1 - hidden_states[-1] ** 2)
            else:
                dl_dh_t = (self.W_ho.T @ dl_dy[t]) + (self.W_hh.T @ dl_dh[0]) * (1 - hidden_states[t] ** 2)

            dl_dh.insert(0, dl_dh_t)

        # 3: Calculate weight gradients using dl_dy and dl_dh
        # Gradient accumulators for each weights matrix:
        # - Weights of hidden to output
        dW_ho = np.zeros_like(self.W_ho)
        # - Weights of input to hidden
        dW_ih = np.zeros_like(self.W_ih)
        # - Weights of hidden to hidden
        dW_hh = np.zeros_like(self.W_hh)

        # - Biases of hidden
        dB_h = np.zeros_like(self.B_h)
        # - Biases of output
        dB_o = np.zeros_like(self.B_o)

        for t in range(len(predictions)):
            dW_ho += dl_dy[t].reshape(-1, 1) @ hidden_states[t].reshape(1, -1)
            dB_o += dl_dy[t]
            dW_ih += dl_dh[t].reshape(-1, 1) @ inputs[t].reshape(1, -1)
            if t == 0:
                dW_hh += dl_dh[t].reshape(-1, 1) @ initial_hidden_state.reshape(1, -1)
            else:
                dW_hh += dl_dh[t].reshape(-1, 1) @ hidden_states[t-1].reshape(1, -1)
            dB_h += dl_dh[t]

        return dW_ih, dW_hh, dW_ho, dB_h, dB_o

    def train(self, inputs, targets, learning_rate, epochs):
        for e in range(epochs):
            # Run a forward pass and get outputs and hidden states
            y, h = self.forward(inputs)
            # See how we're doing!
            loss = calculate_loss(y, targets)
            # Get the gradients to see where we need to update
            dW_ih, dW_hh, dW_ho, dB_h, dB_o = self.backward(y, targets, h, inputs)
            # Apply our updates to our weights...
            self.W_ih -= learning_rate * dW_ih
            self.W_hh -= learning_rate * dW_hh
            self.W_ho -= learning_rate * dW_ho
            # and biases
            self.B_h -= learning_rate * dB_h
            self.B_o -= learning_rate * dB_o

            # See loss every 100 epochs
            if e % 100 == 0:
                print(f"Epoch {e}: loss is {loss}")



def calculate_loss(predictions, targets):
    losses = [a[0] - a[1] for a in zip(predictions, targets)]
    squares = np.array([l ** 2 for l in losses])
    mse = np.mean(squares)

    return mse

if __name__ == "__main__":
    rnn = SimpleRNN(4, 10, 3)
    inputs = np.random.rand(5, 4)

    forward_results = rnn.forward(inputs)

    ys, hs = forward_results

    print(f"Outputs (shapes {ys[0].shape}):")
    for y in ys:
        print(y)

    print(f"\nHiddens (shapes {hs[0].shape}):")
    for h in hs:
        print(h)

